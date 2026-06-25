from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Type

from sqlalchemy.orm import Session

from app.connectors.base import Connector, DiscoveredItem
from app.connectors.local_directory import LocalDirectoryConnector
from app.connectors.local_synced_notes import LocalSyncedNotesConnector
from app.connectors.obsidian_vault import ObsidianVaultConnector
from app.core.settings import SourceConfig
from app.indexing.chunker import ChunkInput, Chunker
from app.indexing.sync import MatchedDocumentChange, detect_changes
from app.models.document import Document
from app.models.index_job import IndexJob
from app.models.source import Source
from app.parsers.base import ParseResult, ParserAdapter
from app.parsers.docx import DocxParser
from app.parsers.html import HtmlParser
from app.parsers.markdown import MarkdownParser
from app.parsers.pdf import PdfParser
from app.parsers.text import TextParser
from app.repositories.documents import DocumentRepository
from app.repositories.index_jobs import IndexJobRepository
from app.repositories.sources import SourceRepository


class UnsupportedConnectorError(ValueError):
    """表示当前数据源类型还没有可用 connector，调用方应把它记录为 source 级失败。"""


class UnsupportedParserError(ValueError):
    """表示当前文件没有匹配的 parser，调用方应只跳过该文件而不是终止整个 source。"""


@dataclass(frozen=True)
class PipelineResult:
    """保存单个文件在索引流水线中的处理结果，便于统计成功和失败数量。"""

    document: Optional[Document]
    error: Optional[str] = None


class IndexingPipeline:
    """串联扫描、增量判断、解析、分块和数据库写入的索引编排器。"""

    def __init__(
        self,
        session: Session,
        parsers: Optional[Sequence[ParserAdapter]] = None,
        chunker: Optional[Chunker] = None,
        connector_types: Optional[Dict[str, Type[Connector]]] = None,
    ) -> None:
        """初始化索引流水线依赖，允许测试或后续云端 connector 注入替换实现。"""
        self.session = session
        self.sources = SourceRepository(session)
        self.documents = DocumentRepository(session)
        self.jobs = IndexJobRepository(session)
        self.parsers = list(parsers or _default_parsers())
        self.chunker = chunker or Chunker()
        self.connector_types = connector_types or _default_connector_types()

    def run_source_index(self, source_id: int) -> IndexJob:
        """对单个数据源执行一次增量索引，并返回可查询的 IndexJob 记录。"""
        source = self.sources.get(source_id)
        if source is None:
            raise ValueError(f"source_not_found: {source_id}")

        job = self.jobs.create(source_id=source.source_id)
        try:
            connector = self._build_connector(source)
            sync_result = connector.scan()
            existing = self.documents.list_snapshots(source.source_id)
            changes = detect_changes(source.source_id, sync_result.items, existing)
            total_items = len(changes.added) + len(changes.updated) + len(changes.deleted)
            processed_items = 0
            failed_items = 0
            errors = list(sync_result.errors)

            for deleted_change in changes.deleted:
                self.documents.update_document_status(
                    deleted_change.existing.document_id,
                    deleted_change.target_status,
                )
                processed_items += 1

            for item in changes.added:
                result = self._index_discovered_item(source.source_id, item)
                if result.error:
                    failed_items += 1
                    errors.append(result.error)
                    continue
                processed_items += 1

            for updated_change in changes.updated:
                result = self._reindex_changed_item(updated_change)
                if result.error:
                    failed_items += 1
                    errors.append(result.error)
                    continue
                processed_items += 1

            status = "completed_with_errors" if errors else "completed"
            return self.jobs.finish(
                job.job_id,
                status=status,
                total_items=total_items,
                processed_items=processed_items,
                failed_items=failed_items,
                errors=errors,
            )
        except Exception as error:
            return self.jobs.mark_failed(job.job_id, str(error))

    def run_all_sources(self) -> List[IndexJob]:
        """遍历所有启用的数据源并逐个执行索引，单个 source 失败不会阻断后续 source。"""
        return [
            self.run_source_index(source.source_id)
            for source in self.sources.list_enabled()
        ]

    def _index_discovered_item(self, source_id: int, item: DiscoveredItem) -> PipelineResult:
        """处理新增文件：选择 parser、写入 document，并生成对应 chunk。"""
        try:
            parse_result = self._parse_item(item)
            document = self.documents.create_document(
                source_id=source_id,
                uri=item.uri,
                title=item.title,
                content_hash=item.content_hash,
                mime_type=item.mime_type,
                metadata_json=_document_metadata(item, parse_result),
            )
            self._write_chunks(document.document_id, parse_result)
            return PipelineResult(document=document)
        except UnsupportedParserError as error:
            return PipelineResult(document=None, error=str(error))

    def _reindex_changed_item(self, change: MatchedDocumentChange) -> PipelineResult:
        """处理内容已变化的文件：替换 document metadata 并重建全部 chunk。"""
        try:
            item = change.discovered
            parse_result = self._parse_item(item)
            document = self.documents.update_document(
                document_id=change.existing.document_id,
                title=item.title,
                content_hash=item.content_hash,
                mime_type=item.mime_type,
                metadata_json=_document_metadata(item, parse_result),
                status="active",
            )
            if document is None:
                return PipelineResult(document=None, error=f"document_not_found: {change.existing.document_id}")

            self.documents.delete_chunks(document.document_id)
            self._write_chunks(document.document_id, parse_result)
            return PipelineResult(document=document)
        except UnsupportedParserError as error:
            return PipelineResult(document=None, error=str(error))

    def _write_chunks(self, document_id: int, parse_result: ParseResult) -> None:
        """把 ParseResult 切分后的 chunk 写入数据库，空文本文件允许没有 chunk。"""
        for chunk in self.chunker.chunk(ChunkInput(parse_result=parse_result, document_id=document_id)):
            self.documents.create_chunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                heading_path=chunk.heading_path,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                metadata_json=chunk.metadata,
            )

    def _parse_item(self, item: DiscoveredItem) -> ParseResult:
        """为扫描条目选择匹配 parser 并执行解析，不支持的文件会抛出可记录错误。"""
        file_path = Path(item.uri)
        parser = self._select_parser(file_path, item.mime_type, item.metadata)
        if parser is None:
            raise UnsupportedParserError(f"unsupported_parser: {item.uri}")
        return parser.parse(file_path)

    def _select_parser(
        self,
        file_path: Path,
        mime_type: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Optional[ParserAdapter]:
        """根据文件扩展名和 MIME 类型选择第一个可处理的 ParserAdapter。"""
        for parser in self.parsers:
            if parser.can_parse(file_path, mime_type=mime_type, metadata=metadata):
                return parser
        return None

    def _build_connector(self, source: Source) -> Connector:
        """根据 Source 记录构造 connector，当前只接入本地优先的三类数据源。"""
        connector_type = self.connector_types.get(source.source_type)
        if connector_type is None:
            raise UnsupportedConnectorError(f"unsupported_connector: {source.source_type}")

        source_config = SourceConfig(
            source_type=source.source_type,
            name=source.name,
            uri=source.uri,
            enabled=source.enabled,
        )
        return connector_type(source_config)


def _default_connector_types() -> Dict[str, Type[Connector]]:
    """返回 MVP 阶段默认支持的本地数据源 connector 映射。"""
    return {
        "local_directory": LocalDirectoryConnector,
        "local_synced_notes": LocalSyncedNotesConnector,
        "obsidian_vault": ObsidianVaultConnector,
    }


def _default_parsers() -> List[ParserAdapter]:
    """返回 MVP 阶段默认启用的 parser 顺序，优先处理轻量文本格式。"""
    return [
        MarkdownParser(),
        TextParser(),
        PdfParser(),
        DocxParser(),
        HtmlParser(),
    ]


def _document_metadata(item: DiscoveredItem, parse_result: ParseResult) -> Dict[str, object]:
    """合并 connector 和 parser metadata，形成可追溯的 document 元数据。"""
    metadata: Dict[str, object] = dict(item.metadata)
    metadata.update(parse_result.metadata)
    metadata.update(
        {
            "mtime": item.mtime,
            "parser_name": parse_result.parser_name,
            "parsed_title": parse_result.title,
            "parser_version": parse_result.parser_version,
            "quality_score": parse_result.quality_score,
            "warnings": list(parse_result.warnings),
            "links": list(parse_result.links),
        }
    )
    return metadata

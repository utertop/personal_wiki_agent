from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.indexing.sync import DocumentSnapshot
from app.models.chunk import Chunk
from app.models.document import Document


class DocumentRepository:
    """封装 Document 和 Chunk 的基础读写操作，供索引流程复用。"""

    def __init__(self, session: Session) -> None:
        """保存当前请求或任务使用的数据库 session。"""
        self.session = session

    def create_document(
        self,
        source_id: int,
        uri: str,
        title: str,
        content_hash: str,
        mime_type: str,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """创建一个标准文档记录，后续 parser 和 chunker 会围绕它继续处理。"""
        document = Document(
            source_id=source_id,
            uri=uri,
            title=title,
            content_hash=content_hash,
            mime_type=mime_type,
            metadata_json=metadata_json or {},
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        text: str,
        heading_path: Optional[str],
        page_number: Optional[int],
        token_count: int,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Chunk:
        """为指定文档创建一个 chunk 记录，保留定位和 token 统计信息。"""
        chunk = Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            heading_path=heading_path,
            page_number=page_number,
            token_count=token_count,
            metadata_json=metadata_json or {},
        )
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return chunk

    def get_document(self, document_id: int) -> Optional[Document]:
        """按主键查询文档；不存在时返回 None。"""
        return self.session.get(Document, document_id)

    def update_document_status(self, document_id: int, status: str) -> Optional[Document]:
        """更新文档状态，例如把缺失文件标记为 deleted。"""
        document = self.get_document(document_id)
        if document is None:
            return None

        document.status = status
        document.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(document)
        return document

    def list_by_source_id(self, source_id: int) -> List[Document]:
        """列出指定数据源的所有文档，包含已删除记录以便追踪状态。"""
        return (
            self.session.query(Document)
            .filter(Document.source_id == source_id)
            .order_by(Document.document_id)
            .all()
        )

    def list_snapshots(self, source_id: int) -> List[DocumentSnapshot]:
        """把数据库文档转换为增量同步所需的轻量快照。"""
        snapshots: List[DocumentSnapshot] = []
        for document in self.list_by_source_id(source_id):
            metadata = document.metadata_json or {}
            snapshots.append(
                DocumentSnapshot(
                    document_id=document.document_id,
                    source_id=document.source_id,
                    uri=document.uri,
                    content_hash=document.content_hash,
                    mtime=metadata.get("mtime"),
                    status=document.status,
                    metadata=metadata,
                )
            )
        return snapshots

    def update_document(
        self,
        document_id: int,
        title: str,
        content_hash: str,
        mime_type: str,
        metadata_json: Optional[Dict[str, Any]] = None,
        status: str = "active",
    ) -> Optional[Document]:
        """更新已有文档的内容指纹和解析 metadata，用于文件变更后重建 chunk。"""
        document = self.get_document(document_id)
        if document is None:
            return None

        document.title = title
        document.content_hash = content_hash
        document.mime_type = mime_type
        document.metadata_json = metadata_json or {}
        document.status = status
        document.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(document)
        return document

    def delete_chunks(self, document_id: int) -> None:
        """删除指定文档已有 chunks，供更新文档时重新写入切分结果。"""
        self.session.query(Chunk).filter(Chunk.document_id == document_id).delete()
        self.session.commit()

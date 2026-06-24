from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.parsers.base import PageMapEntry, ParsedSection, ParseResult


@dataclass(frozen=True)
class ChunkInput:
    """表示 chunker 的输入，封装解析结果和可选的文档标识。"""

    parse_result: ParseResult
    document_id: Optional[int] = None


@dataclass(frozen=True)
class ChunkOutput:
    """表示可写入数据库和检索索引的标准 chunk。"""

    chunk_index: int
    text: str
    heading_path: Optional[str]
    page_number: Optional[int]
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class Chunker:
    """把 ParseResult 切成稳定、可引用、适合检索的 chunk。"""

    def __init__(self, max_chars: int = 1200) -> None:
        """设置单个 chunk 的最大字符数，MVP 阶段先用字符数近似控制长度。"""
        self.max_chars = max_chars

    def chunk(self, chunk_input: ChunkInput) -> List[ChunkOutput]:
        """根据 ParseResult 的结构选择标题、页码或纯文本切分策略。"""
        parse_result = chunk_input.parse_result
        if parse_result.sections:
            return self._chunk_sections(parse_result)
        if parse_result.page_map:
            return self._chunk_pages(parse_result)
        return self._chunk_plain_text(parse_result)

    def _chunk_sections(self, parse_result: ParseResult) -> List[ChunkOutput]:
        """按 section 标题层级切分，并保留 heading_path。"""
        chunks: List[ChunkOutput] = []
        heading_stack: List[ParsedSection] = []

        for section in parse_result.sections:
            heading_stack = [
                existing
                for existing in heading_stack
                if existing.level < section.level
            ]
            heading_stack.append(section)
            heading_path = " / ".join(item.heading for item in heading_stack)

            for text in self._split_text(section.text):
                chunks.append(
                    self._build_chunk(
                        chunk_index=len(chunks),
                        text=text,
                        heading_path=heading_path,
                        page_number=None,
                        parse_result=parse_result,
                    )
                )
        return chunks

    def _chunk_pages(self, parse_result: ParseResult) -> List[ChunkOutput]:
        """按 page_map 切分 PDF 等分页文档，并保留页码。"""
        chunks: List[ChunkOutput] = []
        for page in parse_result.page_map:
            for text in self._split_page_text(page):
                chunks.append(
                    self._build_chunk(
                        chunk_index=len(chunks),
                        text=text,
                        heading_path=None,
                        page_number=page.page_number,
                        parse_result=parse_result,
                    )
                )
        return chunks

    def _chunk_plain_text(self, parse_result: ParseResult) -> List[ChunkOutput]:
        """按段落和长度切分普通文本、HTML 或没有 section 的解析结果。"""
        chunks: List[ChunkOutput] = []
        for text in self._split_text(parse_result.text):
            chunks.append(
                self._build_chunk(
                    chunk_index=len(chunks),
                    text=text,
                    heading_path=None,
                    page_number=None,
                    parse_result=parse_result,
                )
            )
        return chunks

    def _split_page_text(self, page: PageMapEntry) -> List[str]:
        """切分单页文本，避免 PDF 某一页过长。"""
        return self._split_text(page.text)

    def _split_text(self, text: str) -> List[str]:
        """优先按段落组合 chunk，段落仍过长时再按字符窗口切分。"""
        normalized = text.strip()
        if not normalized:
            return []

        chunks: List[str] = []
        current_parts: List[str] = []
        current_length = 0
        for paragraph in _paragraphs(normalized):
            if len(paragraph) > self.max_chars:
                if current_parts:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = []
                    current_length = 0
                chunks.extend(_split_long_text(paragraph, self.max_chars))
                continue

            separator_length = 2 if current_parts else 0
            next_length = current_length + separator_length + len(paragraph)
            if current_parts and next_length > self.max_chars:
                chunks.append("\n\n".join(current_parts))
                current_parts = [paragraph]
                current_length = len(paragraph)
            else:
                current_parts.append(paragraph)
                current_length = next_length

        if current_parts:
            chunks.append("\n\n".join(current_parts))
        return chunks

    def _build_chunk(
        self,
        chunk_index: int,
        text: str,
        heading_path: Optional[str],
        page_number: Optional[int],
        parse_result: ParseResult,
    ) -> ChunkOutput:
        """构造 ChunkOutput，并补齐 token 估算和来源 metadata。"""
        return ChunkOutput(
            chunk_index=chunk_index,
            text=text,
            heading_path=heading_path,
            page_number=page_number,
            token_count=_estimate_token_count(text),
            metadata=dict(parse_result.metadata),
        )


def chunk_document(parse_result: ParseResult) -> List[ChunkOutput]:
    """使用默认 Chunker 切分单个 ParseResult，供索引管线快速调用。"""
    return Chunker().chunk(ChunkInput(parse_result=parse_result))


def _paragraphs(text: str) -> List[str]:
    """把文本按空行拆成段落，并过滤空段。"""
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def _split_long_text(text: str, max_chars: int) -> List[str]:
    """把超过长度上限的段落按字符窗口切开。"""
    return [
        text[index : index + max_chars]
        for index in range(0, len(text), max_chars)
        if text[index : index + max_chars].strip()
    ]


def _estimate_token_count(text: str) -> int:
    """用字符数近似估算 token 数；后续可替换为模型 tokenizer。"""
    compact_text = text.strip()
    if not compact_text:
        return 0
    return max(1, len(compact_text))

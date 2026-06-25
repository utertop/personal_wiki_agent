from app.indexing.chunker import ChunkInput, ChunkOutput, Chunker, chunk_document
from app.parsers.base import PageMapEntry, ParsedSection, ParseResult


def test_chunker_uses_markdown_heading_path() -> None:
    """验证 Markdown 分块会保留标题层级路径。"""

    parse_result = ParseResult(
        title="RAG 笔记",
        text="",
        sections=[
            ParsedSection(heading="RAG 笔记", level=1, text="总览内容"),
            ParsedSection(heading="Agent", level=2, text="Agent 工具调用内容"),
            ParsedSection(heading="检索", level=2, text="Hybrid search 内容"),
        ],
        metadata={"source_format": "markdown"},
    )

    chunks = chunk_document(parse_result)

    assert [chunk.heading_path for chunk in chunks] == [
        "RAG 笔记",
        "RAG 笔记 / Agent",
        "RAG 笔记 / 检索",
    ]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert all(isinstance(chunk, ChunkOutput) for chunk in chunks)
    assert all(chunk.token_count > 0 for chunk in chunks)


def test_chunker_splits_long_plain_text_by_paragraph_and_length() -> None:
    """验证普通长文本会按段落和长度约束切分。"""

    parse_result = ParseResult(
        title="长文本",
        text=(
            "第一段内容比较长，用来验证普通文本可以按长度切分。\n\n"
            "第二段继续补充更多内容，避免一个 chunk 过长。\n\n"
            "第三段保留在后续 chunk 中。"
        ),
        metadata={"source_format": "text"},
    )

    chunks = Chunker(max_chars=42).chunk(ChunkInput(parse_result=parse_result))

    assert len(chunks) >= 2
    assert all(len(chunk.text) <= 42 for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.heading_path is None for chunk in chunks)


def test_chunker_preserves_pdf_page_numbers() -> None:
    """验证 PDF 分块会保留页码信息，方便来源引用。"""

    parse_result = ParseResult(
        title="PDF",
        text="page one text\n\npage two text",
        page_map=[
            PageMapEntry(page_number=1, text="page one text"),
            PageMapEntry(page_number=2, text="page two text"),
        ],
        metadata={"source_format": "pdf"},
    )

    chunks = chunk_document(parse_result)

    assert [chunk.page_number for chunk in chunks] == [1, 2]
    assert [chunk.text for chunk in chunks] == ["page one text", "page two text"]
    assert all(chunk.metadata["source_format"] == "pdf" for chunk in chunks)


def test_chunker_skips_empty_sections_and_empty_text() -> None:
    """验证空章节和空正文不会生成无效 chunk。"""

    parse_result = ParseResult(
        title="空文档",
        text="",
        sections=[ParsedSection(heading="空标题", level=1, text="")],
        metadata={"source_format": "markdown"},
    )

    assert chunk_document(parse_result) == []

from pathlib import Path
from typing import List, Sequence

from app.parsers.base import PageMapEntry, ParseResult, ParserAdapter, empty_result


class PdfParser(ParserAdapter):
    """使用 PyMuPDF 解析 PDF 文本，并保留页码映射。"""

    def parse(self, file_path: Path) -> ParseResult:
        """逐页抽取 PDF 文本，返回全文和 page_map。"""
        path = Path(file_path)
        try:
            import fitz

            document = fitz.open(path)
            page_map: List[PageMapEntry] = []
            for page_index, page in enumerate(document, start=1):
                page_text = page.get_text("text").strip()
                page_map.append(PageMapEntry(page_number=page_index, text=page_text))
            document.close()
        except Exception as error:
            return empty_result(path, "PdfParser", "pdf", ["parse_error: " + str(error)])

        text = "\n\n".join(page.text for page in page_map if page.text)
        warnings = []
        if text == "":
            warnings.append("empty_file")

        return ParseResult(
            title=path.stem,
            text=text,
            page_map=page_map,
            metadata={"source_format": "pdf", "page_count": len(page_map)},
            warnings=warnings,
            parser_name="PdfParser",
            quality_score=0.65,
        )

    @classmethod
    def supported_extensions(cls) -> Sequence[str]:
        """声明 PDF parser 支持的扩展名。"""
        return [".pdf"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        """声明 PDF parser 支持的 MIME 类型。"""
        return ["application/pdf"]

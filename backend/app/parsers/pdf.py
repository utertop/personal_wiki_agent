from pathlib import Path
from typing import List, Sequence

from app.parsers.base import PageMapEntry, ParseResult, ParserAdapter, empty_result


class PdfParser(ParserAdapter):
    def parse(self, file_path: Path) -> ParseResult:
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
        return [".pdf"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return ["application/pdf"]

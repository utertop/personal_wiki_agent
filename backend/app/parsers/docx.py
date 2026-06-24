from pathlib import Path
from typing import List, Sequence

from app.parsers.base import ParsedSection, ParseResult, ParserAdapter, empty_result


class DocxParser(ParserAdapter):
    def parse(self, file_path: Path) -> ParseResult:
        path = Path(file_path)
        try:
            from docx import Document

            document = Document(str(path))
        except Exception as error:
            return empty_result(path, "DocxParser", "docx", ["parse_error: " + str(error)])

        paragraphs = [paragraph for paragraph in document.paragraphs if paragraph.text.strip()]
        text = "\n".join(paragraph.text.strip() for paragraph in paragraphs)
        sections = _extract_sections(paragraphs)
        title = sections[0].heading if sections else path.stem
        warnings = []
        if text == "":
            warnings.append("empty_file")

        return ParseResult(
            title=title,
            text=text,
            sections=sections,
            metadata={"source_format": "docx"},
            warnings=warnings,
            parser_name="DocxParser",
            quality_score=0.65,
        )

    @classmethod
    def supported_extensions(cls) -> Sequence[str]:
        return [".docx"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]


def _extract_sections(paragraphs) -> List[ParsedSection]:
    sections: List[ParsedSection] = []
    for index, paragraph in enumerate(paragraphs):
        style_name = paragraph.style.name if paragraph.style is not None else ""
        if not style_name.startswith("Heading"):
            continue
        level = _heading_level(style_name)
        sections.append(
            ParsedSection(
                heading=paragraph.text.strip(),
                level=level,
                text="",
                line_start=index + 1,
            )
        )
    return sections


def _heading_level(style_name: str) -> int:
    parts = style_name.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return int(parts[-1])
    return 1

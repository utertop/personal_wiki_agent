import re
from pathlib import Path
from typing import List, Sequence

from app.parsers.base import ParsedSection, ParseResult, ParserAdapter, empty_result

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class MarkdownParser(ParserAdapter):
    def parse(self, file_path: Path) -> ParseResult:
        path = Path(file_path)
        try:
            markdown = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return empty_result(path, "MarkdownParser", "markdown", ["decode_error"])
        except OSError as error:
            return empty_result(path, "MarkdownParser", "markdown", ["parse_error: " + str(error)])

        warnings = []
        if markdown == "":
            warnings.append("empty_file")

        sections = _extract_sections(markdown)
        title = sections[0].heading if sections else path.stem
        return ParseResult(
            title=title,
            text=markdown,
            sections=sections,
            links=LINK_PATTERN.findall(markdown),
            metadata={"source_format": "markdown"},
            warnings=warnings,
            markdown=markdown,
            parser_name="MarkdownParser",
            quality_score=0.7,
        )

    @classmethod
    def supported_extensions(cls) -> Sequence[str]:
        return [".md", ".markdown"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return ["text/markdown"]


def _extract_sections(markdown: str) -> List[ParsedSection]:
    lines = markdown.splitlines()
    headings = []
    for index, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match is None:
            continue
        headings.append((index, len(match.group(1)), match.group(2).strip()))

    sections: List[ParsedSection] = []
    for heading_index, (line_index, level, heading) in enumerate(headings):
        next_line_index = headings[heading_index + 1][0] if heading_index + 1 < len(headings) else len(lines)
        text = "\n".join(lines[line_index + 1 : next_line_index]).strip()
        sections.append(
            ParsedSection(
                heading=heading,
                level=level,
                text=text,
                line_start=line_index + 1,
            )
        )
    return sections

from pathlib import Path
from typing import List, Sequence

from app.parsers.base import ParsedSection, ParseResult, ParserAdapter, empty_result


class HtmlParser(ParserAdapter):
    def parse(self, file_path: Path) -> ParseResult:
        path = Path(file_path)
        try:
            html = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return empty_result(path, "HtmlParser", "html", ["decode_error"])
        except OSError as error:
            return empty_result(path, "HtmlParser", "html", ["parse_error: " + str(error)])

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            target = soup.find("article") or soup.body or soup
            text = target.get_text("\n", strip=True)
            links = [tag.get("href") for tag in target.find_all("a", href=True)]
            sections = _extract_sections(target)
            title = _title(soup, sections, path)
        except Exception as error:
            return empty_result(path, "HtmlParser", "html", ["parse_error: " + str(error)])

        warnings = []
        if text == "":
            warnings.append("empty_file")

        return ParseResult(
            title=title,
            text=text,
            sections=sections,
            links=links,
            metadata={"source_format": "html"},
            warnings=warnings,
            markdown=None,
            parser_name="HtmlParser",
            quality_score=0.6,
        )

    @classmethod
    def supported_extensions(cls) -> Sequence[str]:
        return [".html", ".htm"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return ["text/html"]


def _title(soup, sections: List[ParsedSection], path: Path) -> str:
    if soup.title is not None and soup.title.string:
        return soup.title.string.strip()
    if sections:
        return sections[0].heading
    return path.stem


def _extract_sections(target) -> List[ParsedSection]:
    sections: List[ParsedSection] = []
    for tag in target.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        sections.append(
            ParsedSection(
                heading=tag.get_text(" ", strip=True),
                level=level,
                text="",
                line_start=None,
            )
        )
    return sections

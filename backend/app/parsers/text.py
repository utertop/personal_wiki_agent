from pathlib import Path
from typing import Sequence

from app.parsers.base import ParseResult, ParserAdapter, empty_result


class TextParser(ParserAdapter):
    def parse(self, file_path: Path) -> ParseResult:
        path = Path(file_path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return empty_result(path, "TextParser", "text", ["decode_error"])
        except OSError as error:
            return empty_result(path, "TextParser", "text", ["parse_error: " + str(error)])

        warnings = []
        if text == "":
            warnings.append("empty_file")

        return ParseResult(
            title=path.stem,
            text=text,
            metadata={"source_format": "text"},
            warnings=warnings,
            parser_name="TextParser",
            quality_score=0.6,
        )

    @classmethod
    def supported_extensions(cls) -> Sequence[str]:
        return [".txt"]

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return ["text/plain"]

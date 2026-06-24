from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class ParsedSection:
    heading: str
    level: int
    text: str
    line_start: Optional[int] = None


@dataclass(frozen=True)
class PageMapEntry:
    page_number: int
    text: str


@dataclass(frozen=True)
class ParseResult:
    title: str
    text: str
    sections: List[ParsedSection] = field(default_factory=list)
    page_map: List[PageMapEntry] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    markdown: Optional[str] = None
    parser_name: str = ""
    parser_version: str = "0.1.0"
    quality_score: float = 0.5


class ParserAdapter(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> Sequence[str]:
        raise NotImplementedError

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        return []

    @classmethod
    def cost_level(cls) -> str:
        return "low"

    @classmethod
    def quality_level(cls) -> str:
        return "basic"

    def can_parse(
        self,
        file_path: Path,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        path = Path(file_path)
        if path.suffix.lower() in self.supported_extensions():
            return True
        return mime_type in self.supported_mime_types()


def empty_result(
    file_path: Path,
    parser_name: str,
    source_format: str,
    warnings: Optional[List[str]] = None,
) -> ParseResult:
    return ParseResult(
        title=Path(file_path).stem,
        text="",
        metadata={"source_format": source_format},
        warnings=warnings or [],
        parser_name=parser_name,
        quality_score=0.0,
    )

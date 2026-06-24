from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class ParsedSection:
    """表示解析出的标题段落结构，供后续 chunker 按层级切分。"""

    heading: str
    level: int
    text: str
    line_start: Optional[int] = None


@dataclass(frozen=True)
class PageMapEntry:
    """表示 PDF 等分页文档中的单页文本，保留引用页码。"""

    page_number: int
    text: str


@dataclass(frozen=True)
class ParseResult:
    """所有 parser 的统一输出，上层索引流程只消费这个标准结果。"""

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
    """所有文档解析器的抽象接口，用于隔离具体解析库。"""

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """解析文件并返回标准 ParseResult；失败时应返回 warnings 而非抛给上层。"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> Sequence[str]:
        """返回该 parser 支持的文件扩展名。"""
        raise NotImplementedError

    @classmethod
    def supported_mime_types(cls) -> Sequence[str]:
        """返回该 parser 支持的 MIME 类型，默认不声明。"""
        return []

    @classmethod
    def cost_level(cls) -> str:
        """描述解析成本，后续调度器可据此选择轻量或重型 parser。"""
        return "low"

    @classmethod
    def quality_level(cls) -> str:
        """描述解析质量等级，后续可用于触发增强 parser。"""
        return "basic"

    def can_parse(
        self,
        file_path: Path,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """根据扩展名或 MIME 类型判断当前 parser 是否可处理该文件。"""
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
    """构造空解析结果，用于解析失败、空文件或编码异常等非阻断场景。"""
    return ParseResult(
        title=Path(file_path).stem,
        text="",
        metadata={"source_format": source_format},
        warnings=warnings or [],
        parser_name=parser_name,
        quality_score=0.0,
    )

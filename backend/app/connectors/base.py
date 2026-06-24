from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from app.core.settings import SourceConfig


@dataclass(frozen=True)
class DiscoveredItem:
    """表示 connector 扫描到的一个资源条目，还没有进入 parser 和数据库。"""

    uri: str
    title: str
    content_hash: str
    mtime: float
    mime_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SyncResult:
    """表示一次数据源扫描结果，包含发现条目和非阻断错误。"""

    source_type: str
    source_name: str
    items: List[DiscoveredItem]
    errors: List[str] = field(default_factory=list)


class Connector(ABC):
    """所有数据源 connector 的抽象基类，统一扫描入口和忽略规则。"""

    def __init__(
        self,
        source_config: SourceConfig,
        global_ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        """保存数据源配置和全局忽略规则，供具体 connector 复用。"""
        self.source_config = source_config
        self.global_ignore_patterns = list(global_ignore_patterns or [])

    @abstractmethod
    def scan(self) -> SyncResult:
        """扫描数据源并返回标准化结果，具体实现不得直接写数据库。"""
        raise NotImplementedError

    @property
    def ignore_patterns(self) -> List[str]:
        """合并全局和数据源级忽略规则，数据源扫描时统一使用。"""
        return self.global_ignore_patterns + list(self.source_config.ignore_patterns)

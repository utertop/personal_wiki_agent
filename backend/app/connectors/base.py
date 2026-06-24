from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from app.core.settings import SourceConfig


@dataclass(frozen=True)
class DiscoveredItem:
    uri: str
    title: str
    content_hash: str
    mtime: float
    mime_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SyncResult:
    source_type: str
    source_name: str
    items: List[DiscoveredItem]
    errors: List[str] = field(default_factory=list)


class Connector(ABC):
    def __init__(
        self,
        source_config: SourceConfig,
        global_ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        self.source_config = source_config
        self.global_ignore_patterns = list(global_ignore_patterns or [])

    @abstractmethod
    def scan(self) -> SyncResult:
        raise NotImplementedError

    @property
    def ignore_patterns(self) -> List[str]:
        return self.global_ignore_patterns + list(self.source_config.ignore_patterns)

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class SearchQuery:
    """描述一次检索请求，统一承载 query、过滤条件和返回数量。"""

    query: str
    source_id: Optional[int] = None
    document_id: Optional[int] = None
    file_type: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    top_k: int = 10

    @property
    def normalized_query(self) -> str:
        """返回去除首尾空白后的查询文本，空字符串表示无需检索。"""
        return self.query.strip()

    @property
    def candidate_limit(self) -> int:
        """返回底层召回数量，通常比最终 top_k 稍大，便于合并去重。"""
        return max(1, self.top_k) * 2

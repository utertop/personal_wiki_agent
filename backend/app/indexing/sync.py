from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from app.connectors.base import DiscoveredItem


@dataclass(frozen=True)
class DocumentSnapshot:
    """文档表的轻量快照，用于和 connector 扫描结果做差异判断。"""

    document_id: int
    source_id: int
    uri: str
    content_hash: str
    mtime: Optional[float] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchedDocumentChange:
    """表示扫描条目与已有文档匹配后的变化结果。"""

    existing: DocumentSnapshot
    discovered: DiscoveredItem
    reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeletedDocumentChange:
    """表示数据库中存在但本次扫描缺失的文档，默认标记为 deleted。"""

    existing: DocumentSnapshot
    target_status: str = "deleted"


@dataclass(frozen=True)
class MovedDocumentCandidate:
    """表示 content hash 相同但 uri 变化的疑似移动文档。"""

    existing: DocumentSnapshot
    discovered: DiscoveredItem


@dataclass(frozen=True)
class ChangeSet:
    """一次同步差异判断的完整结果，供后续索引编排消费。"""

    source_id: int
    added: List[DiscoveredItem] = field(default_factory=list)
    updated: List[MatchedDocumentChange] = field(default_factory=list)
    deleted: List[DeletedDocumentChange] = field(default_factory=list)
    unchanged: List[MatchedDocumentChange] = field(default_factory=list)
    moved_candidates: List[MovedDocumentCandidate] = field(default_factory=list)


def detect_changes(
    source_id: int,
    discovered_items: Sequence[DiscoveredItem],
    existing_documents: Optional[Sequence[DocumentSnapshot]] = None,
) -> ChangeSet:
    """对比扫描结果和已有文档快照，判断新增、更新、删除和未变化。"""
    existing_for_source = [
        document
        for document in existing_documents or []
        if document.source_id == source_id and document.status != "deleted"
    ]
    existing_by_uri = {document.uri: document for document in existing_for_source}
    seen_uris = set()

    added: List[DiscoveredItem] = []
    updated: List[MatchedDocumentChange] = []
    unchanged: List[MatchedDocumentChange] = []

    for item in discovered_items:
        existing = existing_by_uri.get(item.uri)
        if existing is None:
            added.append(item)
            continue

        seen_uris.add(item.uri)
        reasons = _change_reasons(existing, item)
        if reasons:
            updated.append(MatchedDocumentChange(existing=existing, discovered=item, reasons=reasons))
        else:
            unchanged.append(MatchedDocumentChange(existing=existing, discovered=item))

    deleted = [
        DeletedDocumentChange(existing=document)
        for document in existing_for_source
        if document.uri not in seen_uris
    ]
    moved_candidates = _find_moved_candidates(added, deleted)

    return ChangeSet(
        source_id=source_id,
        added=added,
        updated=updated,
        deleted=deleted,
        unchanged=unchanged,
        moved_candidates=moved_candidates,
    )


def _change_reasons(existing: DocumentSnapshot, item: DiscoveredItem) -> List[str]:
    """返回同一 uri 下触发更新的原因，例如 hash 或 mtime 变化。"""
    reasons: List[str] = []
    if existing.content_hash != item.content_hash:
        reasons.append("content_hash")
    if existing.mtime is not None and existing.mtime != item.mtime:
        reasons.append("mtime")
    return reasons


def _find_moved_candidates(
    added: Sequence[DiscoveredItem],
    deleted: Sequence[DeletedDocumentChange],
) -> List[MovedDocumentCandidate]:
    """根据 content hash 在新增和删除集合之间寻找疑似移动文件。"""
    deleted_by_hash: Dict[str, List[DocumentSnapshot]] = {}
    for change in deleted:
        deleted_by_hash.setdefault(change.existing.content_hash, []).append(change.existing)

    candidates: List[MovedDocumentCandidate] = []
    for item in added:
        for existing in deleted_by_hash.get(item.content_hash, []):
            candidates.append(MovedDocumentCandidate(existing=existing, discovered=item))
    return candidates

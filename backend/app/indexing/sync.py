from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from app.connectors.base import DiscoveredItem


@dataclass(frozen=True)
class DocumentSnapshot:
    document_id: int
    source_id: int
    uri: str
    content_hash: str
    mtime: Optional[float] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchedDocumentChange:
    existing: DocumentSnapshot
    discovered: DiscoveredItem
    reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeletedDocumentChange:
    existing: DocumentSnapshot
    target_status: str = "deleted"


@dataclass(frozen=True)
class MovedDocumentCandidate:
    existing: DocumentSnapshot
    discovered: DiscoveredItem


@dataclass(frozen=True)
class ChangeSet:
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
    deleted_by_hash: Dict[str, List[DocumentSnapshot]] = {}
    for change in deleted:
        deleted_by_hash.setdefault(change.existing.content_hash, []).append(change.existing)

    candidates: List[MovedDocumentCandidate] = []
    for item in added:
        for existing in deleted_by_hash.get(item.content_hash, []):
            candidates.append(MovedDocumentCandidate(existing=existing, discovered=item))
    return candidates

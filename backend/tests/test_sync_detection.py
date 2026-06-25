from app.connectors.base import DiscoveredItem
from app.indexing.sync import DocumentSnapshot, detect_changes


def make_item(uri, content_hash, mtime=100.0):
    """构造测试用扫描条目，模拟 connector 发现的文件。"""

    return DiscoveredItem(
        uri=uri,
        title=uri.rsplit("/", 1)[-1],
        content_hash=content_hash,
        mtime=mtime,
        mime_type="text/markdown",
        metadata={"relative_path": uri.rsplit("/", 1)[-1]},
    )


def make_document(document_id, source_id, uri, content_hash, mtime=100.0, status="active"):
    """构造测试用文档快照，模拟数据库中的已索引文档。"""

    return DocumentSnapshot(
        document_id=document_id,
        source_id=source_id,
        uri=uri,
        content_hash=content_hash,
        mtime=mtime,
        status=status,
    )


def test_detect_changes_marks_all_items_added_without_existing_documents() -> None:
    """验证没有历史文档时，所有扫描条目都会被判定为新增。"""

    item = make_item("E:/Knowledge/new.md", "hash-new")

    changes = detect_changes(source_id=1, discovered_items=[item])

    assert changes.added == [item]
    assert changes.updated == []
    assert changes.deleted == []
    assert changes.unchanged == []


def test_detect_changes_classifies_unchanged_and_updated_documents() -> None:
    """验证增量判断可以区分未变化文档和已更新文档。"""

    unchanged = make_item("E:/Knowledge/same.md", "hash-1", mtime=100.0)
    updated_by_hash = make_item("E:/Knowledge/hash.md", "hash-2", mtime=100.0)
    updated_by_mtime = make_item("E:/Knowledge/mtime.md", "hash-3", mtime=200.0)
    existing = [
        make_document(1, 1, "E:/Knowledge/same.md", "hash-1", mtime=100.0),
        make_document(2, 1, "E:/Knowledge/hash.md", "old-hash", mtime=100.0),
        make_document(3, 1, "E:/Knowledge/mtime.md", "hash-3", mtime=100.0),
    ]

    changes = detect_changes(
        source_id=1,
        discovered_items=[unchanged, updated_by_hash, updated_by_mtime],
        existing_documents=existing,
    )

    assert [change.existing.document_id for change in changes.unchanged] == [1]
    assert [change.existing.document_id for change in changes.updated] == [2, 3]
    assert changes.updated[0].reasons == ["content_hash"]
    assert changes.updated[1].reasons == ["mtime"]


def test_detect_changes_marks_missing_existing_documents_deleted() -> None:
    """验证扫描结果缺失的历史文档会被判定为删除。"""

    item = make_item("E:/Knowledge/keep.md", "hash-keep")
    existing = [
        make_document(1, 1, "E:/Knowledge/keep.md", "hash-keep"),
        make_document(2, 1, "E:/Knowledge/remove.md", "hash-remove"),
    ]

    changes = detect_changes(
        source_id=1,
        discovered_items=[item],
        existing_documents=existing,
    )

    assert [change.existing.document_id for change in changes.deleted] == [2]
    assert changes.deleted[0].target_status == "deleted"


def test_detect_changes_keeps_content_hash_move_candidates() -> None:
    """验证相同内容哈希的新增与删除会被记录为移动候选。"""

    moved_item = make_item("E:/Knowledge/new-location.md", "hash-move")
    existing = [
        make_document(1, 1, "E:/Knowledge/old-location.md", "hash-move"),
    ]

    changes = detect_changes(
        source_id=1,
        discovered_items=[moved_item],
        existing_documents=existing,
    )

    assert changes.added == [moved_item]
    assert [change.existing.document_id for change in changes.deleted] == [1]
    assert len(changes.moved_candidates) == 1
    assert changes.moved_candidates[0].existing.document_id == 1
    assert changes.moved_candidates[0].discovered == moved_item


def test_detect_changes_ignores_documents_from_other_sources() -> None:
    """验证增量判断只处理当前数据源的历史文档。"""

    item = make_item("E:/Knowledge/source-one.md", "hash-1")
    existing = [
        make_document(1, 2, "E:/Knowledge/source-one.md", "hash-1"),
    ]

    changes = detect_changes(
        source_id=1,
        discovered_items=[item],
        existing_documents=existing,
    )

    assert changes.added == [item]
    assert changes.deleted == []

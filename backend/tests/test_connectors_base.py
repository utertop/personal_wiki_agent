import hashlib

from app.connectors.local_directory import LocalDirectoryConnector
from app.connectors.local_synced_notes import LocalSyncedNotesConnector
from app.connectors.obsidian_vault import ObsidianVaultConnector
from app.core.settings import SourceConfig


def make_source(source_type, name, uri, note_app=None, ignore_patterns=None):
    """构造测试用数据源配置，避免各 connector 测试重复样板代码。"""

    return SourceConfig(
        source_type=source_type,
        name=name,
        uri=str(uri),
        note_app=note_app,
        ignore_patterns=ignore_patterns or [],
    )


def test_local_directory_connector_scans_multiple_directories(tmp_path) -> None:
    """验证本地目录 connector 可以扫描多个知识目录。"""

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    (first_root / "rag.md").write_text("RAG 是检索增强生成。", encoding="utf-8")
    nested = second_root / "notes"
    nested.mkdir()
    (nested / "agent.txt").write_text("Agent 笔记", encoding="utf-8")

    first = LocalDirectoryConnector(make_source("local_directory", "资料一", first_root))
    second = LocalDirectoryConnector(make_source("local_directory", "资料二", second_root))

    results = [first.scan(), second.scan()]
    items = [item for result in results for item in result.items]

    assert [result.source_name for result in results] == ["资料一", "资料二"]
    assert sorted(item.title for item in items) == ["agent", "rag"]
    assert all(item.metadata["source_type"] == "local_directory" for item in items)


def test_local_directory_connector_applies_ignore_patterns(tmp_path) -> None:
    """验证本地目录 connector 会同时应用局部和全局忽略规则。"""

    (tmp_path / "keep.md").write_text("保留", encoding="utf-8")
    (tmp_path / "draft.tmp").write_text("忽略", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("secret", encoding="utf-8")
    cache_dir = tmp_path / "nested" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cache.pyc").write_text("cache", encoding="utf-8")

    connector = LocalDirectoryConnector(
        make_source(
            "local_directory",
            "本地资料",
            tmp_path,
            ignore_patterns=["*.tmp"],
        ),
        global_ignore_patterns=[".git/**", "__pycache__/**"],
    )

    result = connector.scan()

    assert [item.title for item in result.items] == ["keep"]
    assert result.items[0].metadata["relative_path"] == "keep.md"


def test_discovered_item_contains_hash_mtime_mime_and_metadata(tmp_path) -> None:
    """验证扫描出的条目包含增量同步所需的元数据。"""

    note = tmp_path / "topic.md"
    content = "主题地图"
    note.write_text(content, encoding="utf-8")
    connector = LocalDirectoryConnector(make_source("local_directory", "本地资料", tmp_path))

    result = connector.scan()
    item = result.items[0]

    assert item.uri == str(note)
    assert item.content_hash == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert item.mtime > 0
    assert item.mime_type in {"text/markdown", "text/plain"}
    assert item.metadata["relative_path"] == "topic.md"
    assert item.metadata["size_bytes"] > 0


def test_local_synced_notes_connector_preserves_note_app_metadata(tmp_path) -> None:
    """验证本地同步笔记 connector 会保留笔记应用标识。"""

    (tmp_path / "youdao.md").write_text("有道云笔记同步内容", encoding="utf-8")
    connector = LocalSyncedNotesConnector(
        make_source("local_synced_notes", "有道同步", tmp_path, note_app="youdao")
    )

    result = connector.scan()

    assert result.source_type == "local_synced_notes"
    assert result.items[0].metadata["source_type"] == "local_synced_notes"
    assert result.items[0].metadata["note_app"] == "youdao"
    assert result.items[0].metadata["sync_mode"] == "local_synced_notes"


def test_obsidian_vault_connector_scans_markdown_and_reserves_note_metadata(tmp_path) -> None:
    """验证 Obsidian vault connector 先扫描 Markdown 并预留笔记元数据。"""

    (tmp_path / "index.md").write_text("# 首页\n[[主题]] #知识库", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"not indexed yet")
    connector = ObsidianVaultConnector(
        make_source("obsidian_vault", "Obsidian", tmp_path, note_app="obsidian")
    )

    result = connector.scan()

    assert [item.title for item in result.items] == ["index"]
    assert result.items[0].metadata["source_type"] == "obsidian_vault"
    assert result.items[0].metadata["front_matter"] == {}
    assert result.items[0].metadata["tags"] == []
    assert result.items[0].metadata["links"] == []

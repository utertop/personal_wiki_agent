from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.settings import load_settings


def test_load_settings_uses_safe_defaults() -> None:
    settings = load_settings(None)

    assert settings.data_dir == Path("data")
    assert settings.database_url == "sqlite:///data/personal_wiki_agent.db"
    assert settings.sources == []
    assert settings.model.chat_provider == "openai-compatible"
    assert settings.privacy.ignore_patterns == []


def test_load_settings_reads_example_config() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "sources.example.yaml"

    settings = load_settings(config_path)

    assert len(settings.sources) == 3
    assert [source.source_type for source in settings.sources] == [
        "local_directory",
        "local_synced_notes",
        "obsidian_vault",
    ]
    assert settings.model.embedding_provider == "openai-compatible"
    assert "*.tmp" in settings.privacy.ignore_patterns


def test_load_settings_rejects_unknown_source_type(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
sources:
  - source_type: unknown_cloud
    name: bad source
    uri: E:/Notes
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_settings(config_path)

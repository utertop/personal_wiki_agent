from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

SourceType = Literal["local_directory", "local_synced_notes", "obsidian_vault"]


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    name: str
    uri: str
    enabled: bool = True
    note_app: Optional[str] = None
    ignore_patterns: List[str] = Field(default_factory=list)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_provider: str = "openai-compatible"
    embedding_provider: str = "openai-compatible"
    local_provider: str = "ollama"


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ignore_patterns: List[str] = Field(default_factory=list)


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_dir: Path = Path("data")
    database_url: str = "sqlite:///data/personal_wiki_agent.db"
    sources: List[SourceConfig] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)


def load_settings(config_path: Optional[Path]) -> AppSettings:
    if config_path is None:
        return AppSettings()

    raw = _read_yaml(config_path)
    return AppSettings.model_validate(raw)


def _read_yaml(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("配置文件顶层必须是 YAML object。")

    return data

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

SourceType = Literal["local_directory", "local_synced_notes", "obsidian_vault"]


class SourceConfig(BaseModel):
    """描述一个数据源配置，例如本地目录、同步笔记目录或 Obsidian vault。"""

    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    name: str
    uri: str
    enabled: bool = True
    note_app: Optional[str] = None
    ignore_patterns: List[str] = Field(default_factory=list)


class ModelInfoConfig(BaseModel):
    """描述配置文件中声明的单个模型及其能力。"""

    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str
    capabilities: List[str]
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    embedding_dimensions: Optional[int] = None
    local: bool = False
    deprecated: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderSettings(BaseModel):
    """描述一个模型 provider 的非敏感配置。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["openai_compatible", "ollama"]
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    enabled: bool = True
    models: List[ModelInfoConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """描述模型供应商配置，后续由 ModelProvider 组件消费。"""

    model_config = ConfigDict(extra="forbid")

    chat_provider: str = "openai-compatible"
    embedding_provider: str = "openai-compatible"
    local_provider: str = "ollama"
    providers: Dict[str, ProviderSettings] = Field(default_factory=dict)
    defaults: Dict[str, str] = Field(default_factory=dict)


class PrivacyConfig(BaseModel):
    """描述隐私相关配置，主要用于排除不应索引的文件或目录。"""

    model_config = ConfigDict(extra="forbid")

    ignore_patterns: List[str] = Field(default_factory=list)


class AppSettings(BaseModel):
    """聚合应用运行所需配置，是后端读取配置文件后的统一对象。"""

    model_config = ConfigDict(extra="forbid")

    data_dir: Path = Path("data")
    database_url: str = "sqlite:///data/personal_wiki_agent.db"
    sources: List[SourceConfig] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)


def load_settings(config_path: Optional[Path]) -> AppSettings:
    """读取 YAML 配置文件；未提供路径时返回安全默认配置。"""
    if config_path is None:
        return AppSettings()

    raw = _read_yaml(config_path)
    return AppSettings.model_validate(raw)


def _read_yaml(config_path: Path) -> Dict[str, Any]:
    """按 UTF-8 读取 YAML，并确保顶层结构是 object。"""
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("配置文件顶层必须是 YAML object。")

    return data

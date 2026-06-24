from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """保存应用级静态配置，后续可扩展为环境变量或配置文件来源。"""

    app_name: str = "Personal Wiki Agent API"

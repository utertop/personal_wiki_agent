from pathlib import Path


def resolve_project_path(path: Path) -> Path:
    """把相对路径解析为绝对路径，避免运行目录变化影响文件定位。"""
    if path.is_absolute():
        return path
    return Path.cwd() / path

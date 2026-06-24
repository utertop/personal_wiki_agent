from pathlib import Path


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path.cwd() / path

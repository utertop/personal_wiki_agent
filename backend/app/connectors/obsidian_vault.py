from pathlib import Path
from typing import Any, Dict, Iterable

from app.connectors.local_directory import LocalDirectoryConnector


class ObsidianVaultConnector(LocalDirectoryConnector):
    def _iter_files(self) -> Iterable[Path]:
        return [
            path
            for path in super()._iter_files()
            if path.suffix.lower() == ".md"
        ]

    def _metadata(self, path: Path, relative_path: str, size_bytes: int) -> Dict[str, Any]:
        metadata = super()._metadata(path, relative_path, size_bytes)
        metadata["source_type"] = "obsidian_vault"
        metadata["front_matter"] = {}
        metadata["tags"] = []
        metadata["links"] = []
        return metadata

from pathlib import Path
from typing import Any, Dict

from app.connectors.local_directory import LocalDirectoryConnector


class LocalSyncedNotesConnector(LocalDirectoryConnector):
    def _metadata(self, path: Path, relative_path: str, size_bytes: int) -> Dict[str, Any]:
        metadata = super()._metadata(path, relative_path, size_bytes)
        metadata["source_type"] = "local_synced_notes"
        metadata["sync_mode"] = "local_synced_notes"
        return metadata

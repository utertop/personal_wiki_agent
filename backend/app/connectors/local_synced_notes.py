from pathlib import Path
from typing import Any, Dict

from app.connectors.local_directory import LocalDirectoryConnector


class LocalSyncedNotesConnector(LocalDirectoryConnector):
    """处理已同步到本机的笔记 App 目录，复用本地目录扫描能力。"""

    def _metadata(self, path: Path, relative_path: str, size_bytes: int) -> Dict[str, Any]:
        """补充同步笔记来源 metadata，保留 note_app 和同步模式。"""
        metadata = super()._metadata(path, relative_path, size_bytes)
        metadata["source_type"] = "local_synced_notes"
        metadata["sync_mode"] = "local_synced_notes"
        return metadata

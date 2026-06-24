from pathlib import Path
from typing import Any, Dict, Iterable

from app.connectors.local_directory import LocalDirectoryConnector


class ObsidianVaultConnector(LocalDirectoryConnector):
    """处理 Obsidian vault，第一版只扫描 Markdown 并预留笔记增强字段。"""

    def _iter_files(self) -> Iterable[Path]:
        """仅返回 Markdown 文件，附件关系留给后续 Obsidian 增强。"""
        return [
            path
            for path in super()._iter_files()
            if path.suffix.lower() == ".md"
        ]

    def _metadata(self, path: Path, relative_path: str, size_bytes: int) -> Dict[str, Any]:
        """补充 Obsidian 专属 metadata 预留位，例如 front matter、标签和双链。"""
        metadata = super()._metadata(path, relative_path, size_bytes)
        metadata["source_type"] = "obsidian_vault"
        metadata["front_matter"] = {}
        metadata["tags"] = []
        metadata["links"] = []
        return metadata

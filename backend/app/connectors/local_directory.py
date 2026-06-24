import fnmatch
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.connectors.base import Connector, DiscoveredItem, SyncResult
from app.core.settings import SourceConfig


class LocalDirectoryConnector(Connector):
    def __init__(
        self,
        source_config: SourceConfig,
        global_ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(source_config, global_ignore_patterns)
        self.root = Path(source_config.uri)

    def scan(self) -> SyncResult:
        items = [
            self._build_item(path)
            for path in self._iter_files()
        ]
        return SyncResult(
            source_type=self.source_config.source_type,
            source_name=self.source_config.name,
            items=items,
        )

    def _iter_files(self) -> Iterable[Path]:
        if not self.root.exists() or not self.root.is_dir():
            return []

        paths: List[Path] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            relative_path = _relative_path(self.root, path)
            if _is_ignored(relative_path, path.name, self.ignore_patterns):
                continue
            paths.append(path)
        return paths

    def _build_item(self, path: Path) -> DiscoveredItem:
        relative_path = _relative_path(self.root, path)
        stat = path.stat()
        return DiscoveredItem(
            uri=str(path),
            title=path.stem,
            content_hash=_sha256_file(path),
            mtime=stat.st_mtime,
            mime_type=_guess_mime_type(path),
            metadata=self._metadata(path, relative_path, stat.st_size),
        )

    def _metadata(self, path: Path, relative_path: str, size_bytes: int) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "source_type": self.source_config.source_type,
            "relative_path": relative_path,
            "size_bytes": size_bytes,
        }
        if self.source_config.note_app is not None:
            metadata["note_app"] = self.source_config.note_app
        return metadata


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_ignored(relative_path: str, file_name: str, patterns: Sequence[str]) -> bool:
    normalized_path = relative_path.replace("\\", "/")
    for pattern in patterns:
        normalized_pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(file_name, normalized_pattern):
            return True
        if fnmatch.fnmatch(normalized_path, normalized_pattern):
            return True
        if normalized_pattern.endswith("/**"):
            directory = normalized_pattern[:-3].strip("/")
            if _path_contains_directory(normalized_path, directory):
                return True
    return False


def _path_contains_directory(relative_path: str, directory: str) -> bool:
    if not directory:
        return False
    parts = relative_path.split("/")
    return directory in parts[:-1]


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if path.suffix.lower() == ".md" and mime_type is None:
        return "text/markdown"
    return mime_type or "application/octet-stream"

import fnmatch
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.connectors.base import Connector, DiscoveredItem, SyncResult
from app.core.settings import SourceConfig


class LocalDirectoryConnector(Connector):
    """递归扫描本地目录，并把文件转换为统一的 DiscoveredItem。"""

    def __init__(
        self,
        source_config: SourceConfig,
        global_ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        """初始化本地目录根路径和忽略规则。"""
        super().__init__(source_config, global_ignore_patterns)
        self.root = Path(source_config.uri)

    def scan(self) -> SyncResult:
        """扫描目录下所有未被忽略的文件，不执行解析和入库。"""
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
        """按稳定顺序递归列出可处理文件，并跳过匹配忽略规则的路径。"""
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
        """把本地文件转换为 DiscoveredItem，并计算 hash、mtime、mime。"""
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
        """构造文件级 metadata，供后续同步判断和 parser 保留来源信息。"""
        metadata: Dict[str, Any] = {
            "source_type": self.source_config.source_type,
            "relative_path": relative_path,
            "size_bytes": size_bytes,
        }
        if self.source_config.note_app is not None:
            metadata["note_app"] = self.source_config.note_app
        return metadata


def _relative_path(root: Path, path: Path) -> str:
    """把文件路径转换为跨平台稳定的 POSIX 相对路径。"""
    return path.relative_to(root).as_posix()


def _is_ignored(relative_path: str, file_name: str, patterns: Sequence[str]) -> bool:
    """判断文件名或相对路径是否命中任一忽略规则。"""
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
    """判断相对路径是否位于指定目录模式下。"""
    if not directory:
        return False
    parts = relative_path.split("/")
    return directory in parts[:-1]


def _sha256_file(path: Path) -> str:
    """分块计算文件 SHA-256，避免大文件一次性读入内存。"""
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _guess_mime_type(path: Path) -> str:
    """根据扩展名推断 MIME 类型，并补齐 Markdown 的常见缺省值。"""
    mime_type, _ = mimetypes.guess_type(str(path))
    if path.suffix.lower() == ".md" and mime_type is None:
        return "text/markdown"
    return mime_type or "application/octet-stream"

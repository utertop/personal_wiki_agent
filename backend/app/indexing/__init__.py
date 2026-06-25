"""Indexing workflow helpers."""

from app.indexing.chunker import ChunkInput, ChunkOutput, Chunker, chunk_document
from app.indexing.lexical import LexicalIndex, SearchFilters, SearchHit
from app.indexing.sync import (
    ChangeSet,
    DeletedDocumentChange,
    DocumentSnapshot,
    MatchedDocumentChange,
    MovedDocumentCandidate,
    detect_changes,
)
from app.indexing.pipeline import (
    IndexingPipeline,
    PipelineResult,
    UnsupportedConnectorError,
    UnsupportedParserError,
)

__all__ = [
    "ChunkInput",
    "ChunkOutput",
    "Chunker",
    "ChangeSet",
    "DeletedDocumentChange",
    "DocumentSnapshot",
    "IndexingPipeline",
    "LexicalIndex",
    "MatchedDocumentChange",
    "MovedDocumentCandidate",
    "PipelineResult",
    "SearchFilters",
    "SearchHit",
    "UnsupportedConnectorError",
    "UnsupportedParserError",
    "chunk_document",
    "detect_changes",
]

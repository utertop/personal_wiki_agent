"""Indexing workflow helpers."""

from app.indexing.chunker import ChunkInput, ChunkOutput, Chunker, chunk_document
from app.indexing.embedding import Embedder, EmbeddingResult, HashingEmbedder
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
from app.indexing.vector_store import (
    InMemoryVectorStore,
    VectorRecord,
    VectorSearchFilters,
    VectorSearchHit,
    VectorStore,
)

__all__ = [
    "ChunkInput",
    "ChunkOutput",
    "Chunker",
    "ChangeSet",
    "DeletedDocumentChange",
    "DocumentSnapshot",
    "Embedder",
    "EmbeddingResult",
    "HashingEmbedder",
    "InMemoryVectorStore",
    "IndexingPipeline",
    "LexicalIndex",
    "MatchedDocumentChange",
    "MovedDocumentCandidate",
    "PipelineResult",
    "SearchFilters",
    "SearchHit",
    "UnsupportedConnectorError",
    "UnsupportedParserError",
    "VectorRecord",
    "VectorSearchFilters",
    "VectorSearchHit",
    "VectorStore",
    "chunk_document",
    "detect_changes",
]

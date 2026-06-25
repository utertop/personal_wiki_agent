from typing import Optional

from sqlalchemy.orm import Session

from app.api.routes_search import SearchResponse, _enrich_search_result
from app.indexing.sqlite_fts import SQLiteFtsIndex
from app.retrieval.filters import SearchQuery
from app.retrieval.hybrid import HybridRetriever


def search_notes(
    session: Session,
    query: str,
    source_id: Optional[int] = None,
    document_id: Optional[int] = None,
    file_type: Optional[str] = None,
    top_k: int = 10,
) -> SearchResponse:
    """为 Agent 提供统一知识库检索工具，返回可追溯来源而不暴露索引细节。"""
    search_query = SearchQuery(
        query=query,
        source_id=source_id,
        document_id=document_id,
        file_type=file_type,
        top_k=top_k,
    )
    if not search_query.normalized_query:
        return SearchResponse(query=query, top_k=top_k, results=[])

    retriever = HybridRetriever(lexical_index=SQLiteFtsIndex(session))
    results = [
        enriched
        for result in retriever.search(search_query)
        for enriched in [_enrich_search_result(session, result, file_type=file_type)]
        if enriched is not None
    ]
    return SearchResponse(query=query, top_k=top_k, results=results)

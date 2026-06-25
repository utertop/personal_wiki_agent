from typing import Iterable, List, TypeVar

T = TypeVar("T")


def combine_scores(
    lexical_score: float,
    vector_score: float,
    lexical_weight: float = 0.5,
    vector_weight: float = 0.5,
) -> float:
    """把关键词分数和向量分数合并为统一排序分数，MVP 阶段先用线性加权。"""
    return lexical_score * lexical_weight + vector_score * vector_weight


def sort_by_score(results: Iterable[T]) -> List[T]:
    """按 score 从高到低排序；score 相同则按 chunk_id 稳定排序。"""
    return sorted(
        results,
        key=lambda result: (-getattr(result, "score"), getattr(result, "chunk_id")),
    )

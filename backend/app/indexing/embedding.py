import hashlib
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    """表示单条文本的 embedding 结果，保留原始顺序以便调用方回填 chunk。"""

    text_index: int
    text: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class Embedder(ABC):
    """embedding 模型的抽象接口，用于隔离 OpenAI、Ollama 或本地测试实现。"""

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> List[EmbeddingResult]:
        """把一批文本转换为向量；返回结果必须与输入文本顺序一一对应。"""
        raise NotImplementedError


class HashingEmbedder(Embedder):
    """无需外部模型的确定性 embedding 实现，用于 MVP 早期测试 VectorStore 契约。"""

    def __init__(self, dimensions: int = 64) -> None:
        """设置向量维度；维度必须为正数，避免后续相似度计算出现空向量。"""
        if dimensions <= 0:
            raise ValueError("dimensions 必须大于 0")
        self.dimensions = dimensions

    def embed_texts(self, texts: Sequence[str]) -> List[EmbeddingResult]:
        """按文本顺序生成稳定向量；它不是语义模型，只用于本地接口闭环。"""
        return [
            EmbeddingResult(
                text_index=index,
                text=text,
                vector=self._embed_one(text),
                metadata={"embedder": "hashing", "dimensions": self.dimensions},
            )
            for index, text in enumerate(texts)
        ]

    def _embed_one(self, text: str) -> List[float]:
        """把文本 token 哈希到固定维度向量，并做 L2 归一化。"""
        tokens = _tokens(text)
        if not tokens:
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        return _normalize(vector)


def _tokens(text: str) -> List[str]:
    """把文本拆成稳定 token；有空白时按词，否则按字符，兼顾中英文最小闭环。"""
    normalized = text.strip().lower()
    if not normalized:
        return []
    whitespace_tokens = [token for token in normalized.split() if token]
    if len(whitespace_tokens) > 1:
        return whitespace_tokens
    return [character for character in normalized if not character.isspace()]


def _normalize(vector: Sequence[float]) -> List[float]:
    """对向量做 L2 归一化，零向量保持全 0。"""
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [value / norm for value in vector]

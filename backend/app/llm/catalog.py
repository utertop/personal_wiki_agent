from typing import Dict, Iterable, List, Optional

from app.llm.provider import ModelInfo


class ModelCatalog:
    """缓存所有 provider 暴露的模型元数据，供 UI、CLI 和 ModelRouter 查询。"""

    def __init__(self, models: Optional[Iterable[ModelInfo]] = None) -> None:
        """初始化 catalog，并把模型按 provider_id/model_id 建立索引。"""
        self._models: Dict[str, ModelInfo] = {}
        for model in models or []:
            self.add_model(model)

    def add_model(self, model: ModelInfo) -> None:
        """新增或替换一个模型信息，使用 full_name 作为稳定键。"""
        self._models[model.full_name] = model

    def get_model(self, full_name: str) -> ModelInfo:
        """按 provider_id/model_id 获取模型，不存在时抛出 KeyError。"""
        return self._models[full_name]

    def find_by_capability(self, capability: str) -> List[ModelInfo]:
        """按能力筛选模型，返回顺序保持注册顺序，便于默认路由稳定。"""
        return [
            model
            for model in self._models.values()
            if model.supports(capability)
        ]

    def has_model(self, full_name: str) -> bool:
        """判断 catalog 中是否存在指定模型。"""
        return full_name in self._models

    def list_models(self) -> List[ModelInfo]:
        """返回 catalog 中所有模型。"""
        return list(self._models.values())

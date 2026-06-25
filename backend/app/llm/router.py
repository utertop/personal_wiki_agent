from dataclasses import dataclass
from typing import Dict, Optional

from app.llm.provider import ModelInfo, ModelProvider
from app.llm.registry import ModelRegistry


class ModelRoutingError(ValueError):
    """表示模型路由失败，例如默认模型不存在或没有模型支持目标任务。"""


@dataclass(frozen=True)
class ModelSelection:
    """表示 ModelRouter 为某个任务选出的 provider 和模型。"""

    task: str
    provider: ModelProvider
    model: ModelInfo

    @property
    def full_name(self) -> str:
        """返回被选中模型的 provider_id/model_id 标识。"""
        return self.model.full_name


class ModelRouter:
    """根据任务类型、默认配置和 catalog 能力为业务层选择模型。"""

    def __init__(self, registry: ModelRegistry, defaults: Optional[Dict[str, str]] = None) -> None:
        """保存 registry 和任务默认模型映射，默认值形如 chat=openai/gpt-x。"""
        self.registry = registry
        self.defaults = dict(defaults or {})

    def select_model(self, task: str) -> ModelSelection:
        """优先使用任务默认模型；未配置时按能力从 catalog 中选择第一个可用模型。"""
        default_model = self.defaults.get(task)
        if default_model is not None:
            if not self.registry.catalog.has_model(default_model):
                raise ModelRoutingError(f"default_model_not_found: {default_model}")
            model = self.registry.catalog.get_model(default_model)
            if not model.supports(task):
                raise ModelRoutingError(f"default_model_not_capable: {default_model}:{task}")
            return self._selection(task, model)

        candidates = self.registry.catalog.find_by_capability(task)
        if not candidates:
            raise ModelRoutingError(f"no_model_for_task: {task}")
        return self._selection(task, candidates[0])

    def _selection(self, task: str, model: ModelInfo) -> ModelSelection:
        """把模型信息转换为包含 provider 实例的路由选择结果。"""
        provider = self.registry.get_provider(model.provider_id)
        return ModelSelection(task=task, provider=provider, model=model)

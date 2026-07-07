from dataclasses import dataclass
import os

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.llm.provider import ModelInfo
from app.main import create_app


class E2EChatModelClient:
    """Stable fake chat model for browser E2E runs."""

    def generate_answer(self, question, context) -> str:
        return "RAG 可以先检索个人知识库资料，再基于引用片段回答问题。"


class E2EProvider:
    provider_id = "e2e"

    def get_chat_client(self, model_id: str) -> E2EChatModelClient:
        return E2EChatModelClient()


@dataclass(frozen=True)
class E2ESelection:
    task: str
    provider: E2EProvider
    model: ModelInfo

    @property
    def full_name(self) -> str:
        return self.model.full_name


class E2EModelRouter:
    def __init__(self) -> None:
        self.provider = E2EProvider()
        self.model = ModelInfo(
            provider_id="e2e",
            model_id="chat",
            display_name="E2E Chat",
            capabilities=["chat"],
        )

    def select_model(self, task: str) -> E2ESelection:
        return E2ESelection(task=task, provider=self.provider, model=self.model)


def create_e2e_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    app = create_app()
    app.state.session_factory = session_factory
    app.state.model_router = E2EModelRouter()
    return app


app = create_e2e_app()


if __name__ == "__main__":
    uvicorn.run(
        "tests.e2e_server:app",
        app_dir="backend",
        host="127.0.0.1",
        port=int(os.environ.get("PERSONAL_WIKI_E2E_API_PORT", "8765")),
        log_level="warning",
    )

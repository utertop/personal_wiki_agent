from app.answer.context_builder import AnswerCitation, AnswerContext, AnswerContextItem
from app.llm.prompt_builder import build_chat_messages


def test_build_chat_messages_includes_sources_and_personalization_memory() -> None:
    """Prompt builder keeps retrieved sources and memory in one shared message shape."""

    context = AnswerContext(
        items=[
            AnswerContextItem(
                text="RAG retrieves personal notes before generating an answer.",
                score=0.91,
                citation=AnswerCitation(
                    document_id=11,
                    chunk_id=22,
                    source_id=33,
                    document_title="RAG Notes",
                    heading_path="Retrieval",
                ),
            )
        ],
        total_results=1,
        personalization_memories=[
            {
                "memory_type": "user_preference",
                "content": "Answer in Chinese when possible.",
            }
        ],
    )

    messages = build_chat_messages("How does RAG help?", context)

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Personal Wiki Agent" in messages[0]["content"]
    user_message = messages[1]["content"]
    assert "How does RAG help?" in user_message
    assert "RAG retrieves personal notes" in user_message
    assert "document_id=11" in user_message
    assert "chunk_id=22" in user_message
    assert "RAG Notes" in user_message
    assert "Retrieval" in user_message
    assert "user_preference" in user_message
    assert "Answer in Chinese when possible." in user_message

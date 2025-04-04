from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks import StdOutCallbackHandler
from typing import Any, Sequence, List, Optional
from uuid import UUID
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document
from langchain_core.outputs import LLMResult

# Keep your custom handler definition here if you plan to switch back
class CustomCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_llm_start:", str(serialized)[:100])

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_llm_end:", str(response.llm_output)[:100])

    def on_chat_model_start(self, serialized, messages, **kwargs):
        print("----------------------------------")
        print("[CustomCallback] Chat model start:", str(messages)[:100])

    def on_chat_model_end(self, response, **kwargs):
        print("----------------------------------")
        print("[CustomCallback] Chat model end:", str(response)[:100])

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, inputs: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_tool_start:", str(serialized)[:100])

    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_tool_end:", str(output)[:100])

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[CustomCallback] on_agent_action: tool: {str(action.tool)[:10]} input: {str(action.tool_input)[:10]}")

    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_agent_finish:", str(finish.return_values)[:10])

    def on_retriever_start(self, serialized: dict[str, Any], query: str, *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_retriever_start:", str(serialized)[:10])

    def on_retriever_end(self, documents: Sequence[Document], *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_retriever_start:", str(documents)[:10])

    def on_custom_event(self, name: str, data: Any, *, run_id: UUID, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[CustomCallback] on_custom_event:", str(data)[:10])


# Singleton instance holder
_callback_handler_instance = None

def get_callback_handler():
    """Gets or creates the callback handler instance."""
    global _callback_handler_instance
    if _callback_handler_instance is None:
        # Switch back to CustomCallbackHandler
        # _callback_handler_instance = StdOutCallbackHandler()
        _callback_handler_instance = CustomCallbackHandler()
        print("DEBUG: Initialized CustomCallbackHandler (in callback_util)")
    return _callback_handler_instance

import asyncio
import json
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler
from typing import Any, Sequence, List, Optional
from uuid import UUID
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document
from langchain_core.outputs import LLMResult
# Assuming ConnectionManager will be defined in main.py or a shared utility
# from main import ConnectionManager # Placeholder import

class WebSocketCallbackHandler(BaseCallbackHandler):
    """Callback handler that sends tool usage events over WebSocket."""

    def __init__(self, websocket_manager: Any): # Use Any for now to avoid circular import
        self.websocket_manager = websocket_manager
        # Get the running event loop when the handler is instantiated
        # This assumes instantiation happens within the FastAPI/Uvicorn context
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # Fallback if no loop is running during instantiation (less likely in FastAPI context)
            self._loop = asyncio.get_event_loop()
        print(f"DEBUG: Initialized WebSocketCallbackHandler with loop: {self._loop}")

    async def _broadcast_tool_event(self, event_type: str, content: str):
        """Helper method to format and broadcast tool events."""
        timestamp = datetime.now().isoformat()
        message = {
            "type": event_type,
            "content": content,
            "timestamp": timestamp
        }
        if self.websocket_manager:
            # Run the broadcast in the event loop managed by FastAPI/Uvicorn
            await self.websocket_manager.broadcast(json.dumps(message))
        else:
            print(f"DEBUG: WebSocket Manager not available. Event: {message}")

    # --- LLM/Chat Model Callbacks (Optional: Keep or remove based on needs) ---
    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[WebSocketCallback] on_llm_start:", str(serialized.get('name', 'Unknown LLM'))[:100])

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        print("----------------------------------")
        # Avoid sending potentially large LLM outputs via WebSocket unless needed
        # print("[WebSocketCallback] on_llm_end:", str(response.llm_output)[:100])

    def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[Any]], **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[WebSocketCallback] Chat model start:", str(serialized.get('name', 'Unknown Chat Model'))[:100])

    # --- Tool Callbacks (Main focus for this task) ---
    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any
    ) -> Any:
        """Send tool start event via WebSocket."""
        print("----------------------------------")
        tool_name = serialized.get('name', 'Unknown Tool')
        description = f"Tool Start: Running tool '{tool_name}' with input: {input_str[:100]}{'...' if len(input_str) > 100 else ''}"
        print(f"[WebSocketCallback] {description}")
        # Schedule the async broadcast method onto the stored event loop
        # using a thread-safe approach.
        asyncio.run_coroutine_threadsafe(
            self._broadcast_tool_event("start", description),
            self._loop
        )

    def on_tool_end(
        self,
        output: Any, # Output is usually a string, but can be other types
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any
    ) -> Any:
        """Send tool end event via WebSocket."""
        print("----------------------------------")
        output_str = str(output)
        description = f"Tool End: Output: {output_str[:200]}{'...' if len(output_str) > 200 else ''}"
        print(f"[WebSocketCallback] {description}")
        asyncio.run_coroutine_threadsafe(
            self._broadcast_tool_event("end", description),
            self._loop
        )

    # --- Agent Callbacks (Optional) ---
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[WebSocketCallback] on_agent_action: tool={action.tool}, input={str(action.tool_input)[:50]}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[WebSocketCallback] on_agent_finish: output={str(finish.return_values)[:100]}")

    # --- Retriever Callbacks (Optional) ---
    def on_retriever_start(self, serialized: dict[str, Any], query: str, **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[WebSocketCallback] on_retriever_start: query={query[:100]}")

    def on_retriever_end(self, documents: Sequence[Document], **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[WebSocketCallback] on_retriever_end: retrieved {len(documents)} documents")

# Removed the singleton logic (get_callback_handler function)
# The handler will be instantiated directly in main.py

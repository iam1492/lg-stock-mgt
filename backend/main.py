import asyncio
import json
from typing import List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os

# Add the parent directory (project root) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from stock_agent.app import graph
    # Import the new WebSocketCallbackHandler
    from stock_agent.utils.callback_util import WebSocketCallbackHandler
except ImportError as e:
    print(f"Error importing graph or WebSocketCallbackHandler: {e}")
    graph = None
    WebSocketCallbackHandler = None # Set to None if import fails

app = FastAPI()

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        print("DEBUG: ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"DEBUG: WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"DEBUG: WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        # Create a list of tasks for sending messages concurrently
        tasks = [connection.send_text(message) for connection in self.active_connections]
        # Wait for all tasks to complete (or handle exceptions)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
             if isinstance(result, Exception):
                 print(f"Error sending message to connection {i}: {result}")
                 # Optionally disconnect the problematic client
                 # self.disconnect(self.active_connections[i]) # Be careful with modifying list while iterating

# Global instance of the Connection Manager
manager = ConnectionManager()

# --- CORS Middleware ---
origins = [
    "http://localhost:3000", # Allow frontend origin
    # Add any other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],
)

# --- WebSocket Endpoint ---
@app.websocket("/ws/tool_usage")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, listening for messages (optional)
            # data = await websocket.receive_text()
            # print(f"Received message via WebSocket: {data}") # Example: echo back
            # await manager.broadcast(f"Client message: {data}")
            await asyncio.sleep(1) # Prevent busy-waiting if not actively receiving
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("DEBUG: WebSocket client disconnected.")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        manager.disconnect(websocket)


# --- Stream Request Model ---
class StreamRequest(BaseModel):
    company: str
    user_input: str | None = None

# --- Event Generator for Streaming ---
async def event_generator(company: str, user_input: str, websocket_manager: ConnectionManager):
    """
    Generates server-sent events from the LangGraph stream and uses WebSocket callback.
    """
    if graph is None or WebSocketCallbackHandler is None:
        yield f"data: {json.dumps({'error': 'Graph or Callback Handler not loaded'})}\n\n"
        return

    # Instantiate the WebSocketCallbackHandler with the manager
    callback_handler = WebSocketCallbackHandler(websocket_manager)
    config = {"callbacks": [callback_handler]}
    print("DEBUG: Using WebSocketCallbackHandler for graph.astream.")

    # Construct the initial message
    input_message = user_input if user_input else f"Analyze {company} stock."
    initial_state = {"messages": [HumanMessage(content=input_message)], "company": company}

    print(f"DEBUG: Entering event_generator for company: {company}")
    try:
        print("DEBUG: Starting graph.astream with WebSocket callback...")
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
            try:
                if isinstance(event, dict):
                    for node_name, update_value in event.items():
                        if isinstance(update_value, dict) and 'messages' in update_value:
                            new_messages = update_value['messages']
                            for msg in new_messages:
                                if isinstance(msg, AIMessage):
                                    content_to_send = None
                                    if hasattr(msg, 'content'):
                                        content_to_send = str(msg.content)
                                    elif hasattr(msg, 'dict'):
                                        msg_dict = msg.dict()
                                        if 'content' in msg_dict:
                                            content_to_send = str(msg_dict['content'])

                                    if content_to_send:
                                        formatted_content = f"{node_name}: {content_to_send}"
                                        json_data = json.dumps({"content": formatted_content})
                                        yield f"data: {json_data}\n\n"
            except Exception as e:
                print(f"Error processing stream event: {e}. Event: {event}")
                error_content = json.dumps({'error': 'Error processing stream event', 'details': str(e)})
                yield f"data: {json.dumps({'content': error_content})}\n\n"
            await asyncio.sleep(0.01)

        print("DEBUG: Graph stream finished.")
    except Exception as e:
        print(f"ERROR during graph stream: {e}")
        error_content = json.dumps({'error': 'Error during stream execution', 'details': str(e)})
        yield f"data: {json.dumps({'content': error_content})}\n\n"
    finally:
        print("DEBUG: Exiting event_generator.")


# --- HTTP Stream Endpoint ---
@app.post("/stream_endpoint")
async def stream_endpoint(request_data: StreamRequest):
    """
    API endpoint to stream LangGraph execution results via SSE.
    Uses the global WebSocket manager for the callback handler.
    """
    company = request_data.company
    user_input = request_data.user_input
    # Pass the global manager instance to the generator
    return StreamingResponse(event_generator(company, user_input, manager), media_type="text/event-stream")

# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "LangGraph Stock Agent API with WebSocket Support"}

# --- Server Execution ---
# Example: uvicorn backend.main:app --reload --port 8080
# Ensure the port matches the frontend fetch and WebSocket URLs (default 8080 used here)

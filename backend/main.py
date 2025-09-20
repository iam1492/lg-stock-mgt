import asyncio
import json
from typing import List
from contextlib import asynccontextmanager # Import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os
from fastapi_utilities import repeat_at # Use repeat_at for cron scheduling

# Add the parent directory (project root) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to be scheduled
try:
    from backend.macro_job import save_macro_economics
except ImportError as e:
    print(f"Error importing save_macro_economics: {e}")
    save_macro_economics = None # Set to None if import fails

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


# --- Scheduled Task Function ---
# Moved the scheduling logic into a separate async function
@repeat_at(cron="0 0 * * *", raise_exceptions=True) # Run daily at midnight using repeat_at
async def schedule_macro_job() -> None:
    """
    Schedules the save_macro_economics function to run daily at midnight.
    """
    if save_macro_economics:
        print("INFO: Running scheduled task: save_macro_economics")
        try:
            # Assuming save_macro_economics is synchronous.
            # If it'`s async, use 'await save_macro_economics()'
            # Consider running synchronous blocking code in a thread pool executor
            # if it might block the asyncio event loop for too long.
            # For now, calling it directly.
            # save_macro_economics()
            print("INFO: Scheduled task save_macro_economics completed successfully.")
        except Exception as e:
            print(f"ERROR: Scheduled task save_macro_economics failed: {e}")
    else:
        print("ERROR: save_macro_economics function not loaded, skipping scheduled task.")

# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("INFO: Starting up FastAPI application...")

    # --- Run save_macro_economics once on startup ---
    if save_macro_economics:
        print("INFO: Running initial save_macro_economics on startup...")
        try:
            # Call the synchronous function directly.
            # Consider running in a thread pool if it's long-running to avoid blocking startup.
            # save_macro_economics()
            print("INFO: Initial save_macro_economics completed.")
        except Exception as e:
            print(f"ERROR: Initial save_macro_economics failed: {e}")
    else:
        print("ERROR: save_macro_economics function not loaded, skipping initial run.")
    # -------------------------------------------------

    # Start the recurring scheduled task
    asyncio.create_task(schedule_macro_job())
    print("INFO: Scheduled macro job task created for daily execution.")
    yield
    # Code to run on shutdown (optional)
    print("INFO: Shutting down FastAPI application...")

# --- FastAPI App Initialization with Lifespan ---
app = FastAPI(lifespan=lifespan)

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
    "http://127.0.0.1:3000",
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

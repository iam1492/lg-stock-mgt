import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import sys
import os

# Add the parent directory (project root) to the Python path
# to allow importing from stock_agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import the graph from the stock_agent application
    from stock_agent.app import graph
except ImportError as e:
    print(f"Error importing graph from stock_agent.app: {e}")
    # Provide a dummy graph or raise an error if the import fails
    # This helps in identifying path issues early
    graph = None # Or raise RuntimeError("Could not import graph") from e

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:3000", # Allow frontend origin
    # Add any other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Allow all headers
)


class StreamRequest(BaseModel):
    company: str
    user_input: str | None = None # Optional user input, defaults if not provided

async def event_generator(company: str, user_input: str):
    """
    Generates server-sent events from the LangGraph stream.
    """
    if graph is None:
        yield f"data: {json.dumps({'error': 'Graph not loaded'})}\n\n"
        return

    # Construct the initial message for the graph stream
    input_message = user_input if user_input else f"Do a research and Analyze {company} stock."
    initial_state = {
        "messages": [HumanMessage(content=input_message)],
        "company": company
    }

    try:
        # Stream the graph execution
        async for event in graph.astream(initial_state, stream_mode="values"):
            # Ensure the event is JSON serializable
            # Process different event structures if necessary
            if isinstance(event, dict):
                # Attempt to serialize the event dictionary
                try:
                    # Convert message objects if they exist and are not serializable
                    if 'messages' in event and event['messages']:
                         # Convert last message to dict for streaming if possible
                         last_message = event['messages'][-1]
                         if hasattr(last_message, 'dict'):
                             event_data = last_message.dict()
                         elif hasattr(last_message, 'content'):
                              event_data = {"content": last_message.content, "type": type(last_message).__name__}
                         else:
                             event_data = str(last_message) # Fallback
                    else:
                        event_data = event # Stream the whole event dict if no messages or simple structure

                    json_data = json.dumps(event_data)
                    yield f"data: {json_data}\n\n"
                except TypeError as e:
                    # Handle cases where parts of the event are not serializable
                    print(f"Serialization Error: {e}. Event part causing issue: {event_data}")
                    yield f"data: {json.dumps({'error': 'Non-serializable data in stream', 'details': str(e)})}\n\n"
            else:
                 # Handle non-dict events if necessary
                 yield f"data: {json.dumps({'raw_event': str(event)})}\n\n"

            await asyncio.sleep(0.01) # Small delay to prevent blocking

        # Signal the end of the stream
        yield f"data: {json.dumps({'status': 'Stream ended'})}\n\n"

    except Exception as e:
        print(f"Error during graph stream: {e}")
        yield f"data: {json.dumps({'error': 'Error during stream execution', 'details': str(e)})}\n\n"


# Note: The endpoint path in the frontend fetch request is /stream_endpoint
# Ensure this matches the path defined here. Let's change it to match the frontend.
@app.post("/stream_endpoint")
async def stream_endpoint(request_data: StreamRequest):
    """
    API endpoint to stream LangGraph execution results.
    Accepts a company name and optional user input.
    """
    company = request_data.company
    user_input = request_data.user_input
    return StreamingResponse(event_generator(company, user_input), media_type="text/event-stream")

@app.get("/")
async def read_root():
    return {"message": "LangGraph Stock Agent API"}

# Example of how to run this server using uvicorn:
# uvicorn backend.main:app --reload --port 8000

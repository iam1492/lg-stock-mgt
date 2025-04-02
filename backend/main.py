import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
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

    target_agents = {
    }
    # processed_message_ids = set() # No longer needed with stream_mode="updates"
    print(f"DEBUG: Entering event_generator for company: {company}")

    try:
        print("DEBUG: About to start graph.astream loop with stream_mode='updates'...")
        # Stream the graph execution using "updates" mode
        async for event in graph.astream(initial_state, stream_mode="updates"):
            print(f"DEBUG: Received update event: {event}") # Log the raw update event
            try:
                # Events in "updates" mode are dicts like: {"node_name": {"messages": [AIMessage]}}
                if isinstance(event, dict):
                    for node_name, update_value in event.items():
                        # Check if the update contains new messages
                        if isinstance(update_value, dict) and 'messages' in update_value:
                            new_messages = update_value['messages']
                            # Process only the new AIMessages from this update
                            for msg in new_messages:
                                if isinstance(msg, AIMessage):
                                    content_to_send = None
                                    if hasattr(msg, 'content'):
                                        content_to_send = str(msg.content)
                                    elif hasattr(msg, 'dict'): # Fallback
                                        msg_dict = msg.dict()
                                        if 'content' in msg_dict:
                                            content_to_send = str(msg_dict['content'])

                                    if content_to_send:
                                        # Prepend the node name (agent name)
                                        formatted_content = f"{node_name}: {content_to_send}"
                                        json_data = json.dumps({"content": formatted_content})
                                        print(f"DEBUG: Yielding content from node '{node_name}'")
                                        yield f"data: {json_data}\n\n"
                                        print(f"DEBUG: Finished yielding content from node '{node_name}'")

            except Exception as e: # Corrected indentation
                # Handle serialization or processing errors for this specific event
                print(f"Error processing event: {e}. Event: {event}")
                # Send error details wrapped in the standard content structure
                error_content = json.dumps({'error': 'Error processing stream event', 'details': str(e)})
                yield f"data: {json.dumps({'content': error_content})}\n\n"

            await asyncio.sleep(0.01) # Small delay to prevent blocking

        # Signal the end of the stream (optional, but can be useful)
        print("DEBUG: Graph stream finished.") # DEBUG After loop
        # yield f"data: {json.dumps({'content': '**Stream ended.**'})}\n\n" # Send as content

    except Exception as e:
        print(f"ERROR during graph stream: {e}") # DEBUG Error in loop
        # Send error details wrapped in the standard content structure
        error_content = json.dumps({'error': 'Error during stream execution', 'details': str(e)})
        yield f"data: {json.dumps({'content': error_content})}\n\n"
    finally:
        print("DEBUG: Exiting event_generator.") # DEBUG End of function


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

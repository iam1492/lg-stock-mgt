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
    # Import the getter function for the handler from the util file
    from stock_agent.utils.callback_util import get_callback_handler
except ImportError as e:
    print(f"Error importing graph or get_callback_handler: {e}") # Adjusted error message
    graph = None
    get_callback_handler = None # Set getter to None if import fails

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

    # Prepare config for astream, getting the handler via the getter
    config = {}
    if get_callback_handler:
        try:
            handler = get_callback_handler() # Call the getter function
            if handler:
                config = {"callbacks": [handler]}
                print("DEBUG: Using callback handler obtained via getter for graph.astream.")
            else:
                 print("WARN: get_callback_handler() returned None.")
        except Exception as e:
            print(f"ERROR: Failed to get callback handler: {e}")
            print("WARN: Proceeding without graph execution callbacks.")
    else:
        print("WARN: get_callback_handler function not imported, proceeding without graph execution callbacks.")

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
        print("DEBUG: About to start graph.astream loop with stream_mode='updates' and config...")
        # Pass the potentially populated config to astream
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
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
                    
                                        yield f"data: {json_data}\n\n"

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

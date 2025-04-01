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
            content_to_send = None
            try:
                if isinstance(event, dict):
                    # Prioritize content from the last message
                    if 'messages' in event and event['messages']:
                        last_message = event['messages'][-1]
                        if hasattr(last_message, 'content'):
                            content_to_send = str(last_message.content) # Ensure it's a string
                        elif hasattr(last_message, 'dict'):
                             msg_dict = last_message.dict()
                             if 'content' in msg_dict:
                                 content_to_send = str(msg_dict['content'])

                    # Fallback: If no content found in messages, serialize the event dict itself.
                    # This helps diagnose the structure but might display raw JSON in frontend.
                    # TODO: Refine this based on actual graph output structure if needed.
                    if content_to_send is None:
                         # Attempt to prevent sending overly complex/large states if possible
                         # For example, only send specific keys if known
                         keys_to_try = ['agent_output', 'response', 'result'] # Example keys
                         found_key = False
                         for key in keys_to_try:
                             if key in event:
                                 content_to_send = json.dumps({key: event[key]}, indent=2)
                                 found_key = True
                                 break
                         if not found_key:
                             # Avoid sending the full 'messages' list back again if possible
                             simple_event = {k: v for k, v in event.items() if k != 'messages'}
                             content_to_send = json.dumps(simple_event, indent=2)


                else:
                    # Handle non-dict events by converting to string
                    content_to_send = str(event)

                if content_to_send is not None:
                    # Always wrap the content in the expected JSON structure {"content": ...}
                    json_data = json.dumps({"content": content_to_send})
                    yield f"data: {json_data}\n\n"

            except Exception as e:
                # Handle serialization or processing errors for this specific event
                print(f"Error processing event: {e}. Event: {event}")
                # Send error details wrapped in the standard content structure
                error_content = json.dumps({'error': 'Error processing stream event', 'details': str(e)})
                yield f"data: {json.dumps({'content': error_content})}\n\n"

            await asyncio.sleep(0.01) # Small delay to prevent blocking

        # Signal the end of the stream (optional, but can be useful)
        # yield f"data: {json.dumps({'content': '**Stream ended.**'})}\n\n" # Send as content

    except Exception as e:
        print(f"Error during graph stream: {e}")
        # Send error details wrapped in the standard content structure
        error_content = json.dumps({'error': 'Error during stream execution', 'details': str(e)})
        yield f"data: {json.dumps({'content': error_content})}\n\n"


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

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

def create_agent_node(state, llm , system_prompt):
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    other_messages = [msg for msg in state["messages"] 
                     if not isinstance(msg, HumanMessage) and not isinstance(msg, SystemMessage)]
    system_messages = [SystemMessage(content=system_prompt)]
    messages = system_messages + human_messages + other_messages
    message = llm.invoke(messages)
    
    return {
        "messages": [message]
    }
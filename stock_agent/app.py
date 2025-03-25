from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from graph.display_graph import save_mermaid_as_png
from agents import researcher, financial_analyst, financial_analyst_2, financial_advisor, hedge_fund_manager

load_dotenv()

_openai = ChatOpenAI (
    model= "gpt-4o-mini"
)

class State(MessagesState):
    company: str

# #researcher = lambda state: create_agent_node(state, llm, system_prompt=stock_researcher_prompt)
# financial_analyst_2 = lambda state: create_agent_node(state, llm, system_prompt=stock_financial_analyst_2_prompt)
# financial_advisor = lambda state: create_agent_node(state, llm, system_prompt=stock_financial_advisor_prompt)
# hedge_fund_manager = lambda state: create_agent_node(state, llm, system_prompt=hedge_fund_manager_prompt)

# financial_analyst_subgraph = get_financial_analyst_subgraph()

builder = StateGraph(State)
builder.add_node("researcher", researcher)
builder.add_node("financial_analyst", financial_analyst)
builder.add_node("financial_analyst_2", financial_analyst_2)
builder.add_node("financial_advisor", financial_advisor)
builder.add_node("hedge_fund_manager", hedge_fund_manager)

builder.add_edge(START, "researcher")
builder.add_edge("researcher", "financial_analyst")
builder.add_edge("researcher", "financial_analyst_2")

builder.add_edge(["financial_analyst", "financial_analyst_2"], "financial_advisor")
builder.add_edge("financial_advisor", "hedge_fund_manager")
builder.add_edge("hedge_fund_manager", END)

graph = builder.compile()

save_mermaid_as_png(graph)

def main_loop():
    print(f"Starting...")
    company = "Tesla"
    user_input = f"Do a research and Analyze {company} stock."
    initial_message = {
            "messages": [HumanMessage(content=user_input)],
            "company": company
        }
    for event in graph.stream(initial_message, stream_mode="values"):
            event['messages'][-1].pretty_print()
    # while True:
    #     user_input = input(">> ")
    #     if user_input.lower() in ["quit", "exit", "q"]:
    #         print("Goodbye!")
    #         break
        
    #     initial_message = {
    #         "messages": [HumanMessage(content=user_input)]
    #     }
    
    #     for event in app.stream(initial_message, stream_mode="values"):
    #         event['messages'][-1].pretty_print()

if __name__ == "__main__":
    main_loop()
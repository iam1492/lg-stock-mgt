#!/usr/bin/env python
# -*- coding: utf-8 -*-

from stock_agent.app import graph
from langchain_core.messages import HumanMessage
import sys

def test_translator_workflow():
    """Test the complete workflow with translator"""
    print("Testing LangGraph Stock Analysis System with Translator...")

    company = "Apple Inc."
    user_input = f"Do a research and analyze {company} stock."

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "company": company
    }

    print(f"Starting analysis for {company}...")
    print("=" * 50)

    try:
        # Run only the hedge fund manager and translator for quick testing
        # This is a simplified test - in full execution, all agents would run
        for event in graph.stream(initial_state, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_message = event["messages"][-1]
                print(f"\n--- {getattr(last_message, 'name', 'Agent')} ---")
                print(last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content)

    except Exception as e:
        print(f"Error during execution: {e}")
        return False

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    return True

if __name__ == "__main__":
    # Set UTF-8 encoding for console output
    if sys.platform.startswith('win'):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

    test_translator_workflow()
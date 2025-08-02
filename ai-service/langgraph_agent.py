"""
LangGraph agent for handling conversation flow
"""

from typing import Any, Dict, Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from config import TRANSPARENCY_QUESTIONS

# Agent State
class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    product_id: str
    current_question: int
    questions: list[str]
    responses: list[str]
    scores: list[int]
    context: Dict[str, Any]
    final_score: float
    is_complete: bool

def ask_question_node(state: State):
    """Node for asking transparency questions"""
    if state["current_question"] <= 6:
        question = TRANSPARENCY_QUESTIONS[state["current_question"] - 1]
        state["messages"].append({"role": "assistant", "content": question})
    return state

def process_response_node(state: State):
    """Node for processing user responses"""
    if state["current_question"] > 6:
        state["is_complete"] = True
        if state["scores"]:
            state["final_score"] = sum(state["scores"]) / len(state["scores"])
    return state

def should_continue(state: State):
    """Decide whether to continue or end"""
    if state["is_complete"] or state["current_question"] > 6:
        return "end"
    return "continue"

# Create LangGraph workflow
def create_workflow():
    """Create and return compiled LangGraph workflow"""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("ask_question", ask_question_node)
    workflow.add_node("process_response", process_response_node)

    # Add edges
    workflow.add_edge(START, "ask_question")
    workflow.add_edge("ask_question", "process_response")

    # Add conditional edges
    workflow.add_conditional_edges(
        "process_response",
        should_continue,
        {
            "continue": "ask_question",
            "end": END
        }
    )

    # Compile and return the graph
    return workflow.compile()

# Create the compiled workflow
app_graph = create_workflow()
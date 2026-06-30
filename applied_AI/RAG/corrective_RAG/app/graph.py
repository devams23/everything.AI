from langgraph.graph import StateGraph, END
from app.state import GraphState
from app.retrieval import retrieve_top_k
from app.evaluation import evaluate_documents
from app.routing import route_documents
from app.fallback import fallback_and_assemble
from app.generation import generate_response

def build_crag_graph():
    workflow = StateGraph(GraphState)
    
    # Nodes
    workflow.add_node("retrieve", retrieve_top_k)
    workflow.add_node("evaluate", evaluate_documents)
    workflow.add_node("fallback", fallback_and_assemble)
    workflow.add_node("generate", generate_response)
    
    # Edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "evaluate")
    
    workflow.add_conditional_edges(
        "evaluate",
        route_documents,
        {
            "generate": "generate",
            "fallback": "fallback"
        }
    )
    
    workflow.add_edge("fallback", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

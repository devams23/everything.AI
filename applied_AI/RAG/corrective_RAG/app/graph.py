from langgraph.graph import StateGraph, END
from app.state import GraphState
from app.retrieval import retrieve_top_k
from app.evaluation import evaluate_documents
from app.routing import route_documents
from app.knowledge import knowledge_refine, web_search, ambiguous_process
from app.generation import generate_response

def build_crag_graph():
    workflow = StateGraph(GraphState)
    
    # Nodes
    workflow.add_node("retrieve", retrieve_top_k)
    workflow.add_node("evaluate", evaluate_documents)
    workflow.add_node("knowledge_refine", knowledge_refine)
    workflow.add_node("web_search", web_search)
    workflow.add_node("ambiguous_process", ambiguous_process)
    workflow.add_node("generate", generate_response)
    
    # Edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "evaluate")
    
    workflow.add_conditional_edges(
        "evaluate",
        route_documents,
        {
            "knowledge_refine": "knowledge_refine",
            "web_search": "web_search",
            "ambiguous_process": "ambiguous_process"
        }
    )
    
    workflow.add_edge("knowledge_refine", "generate")
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("ambiguous_process", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

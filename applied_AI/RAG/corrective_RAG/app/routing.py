def route_documents(state):
    """
    Orchestration & Decision Routing
    Path A: Correct
    Path B: Ambiguous
    Path C: Incorrect
    """
    docs = state.documents
    
    if not docs:
        return "fallback"
        
    first_doc_score = docs[0].metadata.get("score", 0.0)
    
    if first_doc_score >= 0.8:
        # Path A: Correct
        return "generate"
    elif 0.4 <= first_doc_score < 0.8:
        # Path B: Ambiguous (Partial/Insufficient Context)
        return "fallback"
    else:
        # Path C: Incorrect (Irrelevant or Stale Data)
        return "fallback"

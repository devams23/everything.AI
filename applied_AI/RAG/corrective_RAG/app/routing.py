def route_documents(state):
    """
    Routes based on the Confidence judgment from the evaluation step.
    Returns the name of the next node.
    """
    confidence = state.get("confidence", "INCORRECT")
    
    if confidence == "CORRECT":
        return "knowledge_refine"
    elif confidence == "INCORRECT":
        return "web_search"
    else:
        return "ambiguous_process"

import time
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document

EXTERNAL_SEARCH_CACHE = {}

def query_expansion(query: str) -> str:
    # Dummy expansion
    return query + " synonyms related"

def external_search_cache(query: str):
    if query in EXTERNAL_SEARCH_CACHE:
        entry = EXTERNAL_SEARCH_CACHE[query]
        # TTL 1 Hour
        if time.time() - entry['time'] < 3600:
            return entry['data']
    return None

def fallback_and_assemble(state):
    """
    Knowledge Validation & External Fallback
    """
    query = state.query
    expanded_query = query_expansion(query)
    
    # 1. Check Cache
    cached_result = external_search_cache(expanded_query)
    
    if cached_result:
        external_docs = cached_result
    else:
        # 2. Circuit Breaker
        start_time = time.time()
        
        try:
            tool = TavilySearchResults(max_results=3)
            # In a real scenario, this could block for 30s.
            results = tool.invoke({"query": expanded_query})
            
            elapsed = time.time() - start_time
            if elapsed > 3.0:
                # Rate Limit / Timeout -> Graceful Degradation
                external_docs = [Document(page_content="Stale external data", metadata={"tag": "EXTERNAL", "status": "stale"})]
            else:
                external_docs = [Document(page_content=r["content"], metadata={"tag": "EXTERNAL"}) for r in results]
                
            EXTERNAL_SEARCH_CACHE[expanded_query] = {"time": time.time(), "data": external_docs}
            
        except Exception as e:
            external_docs = [Document(page_content="Fallback failed", metadata={"tag": "EXTERNAL", "status": "stale"})]
            
    # 3. Context Assembler
    assembled_docs = []
    for doc in external_docs:
        doc.metadata["source_type"] = "EXTERNAL"
        assembled_docs.append(doc)
        
    return {"documents": assembled_docs, "external_context": assembled_docs}

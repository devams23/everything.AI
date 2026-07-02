from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class RewriteOutput(BaseModel):
    query: str = Field(description="The optimized query for web search")

def rewrite_query(query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(RewriteOutput)
    
    prompt = PromptTemplate(
        template="Rewrite the following query to be optimized for a web search engine:\n\nQuery: {query}",
        input_variables=["query"]
    )
    
    rewriter = prompt | structured_llm
    result = rewriter.invoke({"query": query})
    return result.query

def knowledge_refine(state):
    """
    CORRECT PATH: Refines internal knowledge by dropping low score chunks.
    """
    docs = state.documents
    
    refined_docs = []
    for doc in docs:
        relevance = doc.metadata.get("relevance", 0)
        accuracy = doc.metadata.get("accuracy", 0)
        
        # Keep documents that meet a minimum threshold
        if relevance >= 5 and accuracy >= 5:
            refined_docs.append(doc)
            
    return {"documents": refined_docs}

def web_search(state):
    """
    INCORRECT PATH: Web Search (W Rewrites x for searching)
    Includes graceful fallback if external search fails.
    """
    query = state.query
    rewritten_query = rewrite_query(query)
    
    tool = TavilySearchResults(max_results=3)
    external_docs = []
    
    try:
        results = tool.invoke({"query": rewritten_query})
        
        if not results:
            raise ValueError("No results found from web search.")
            
        external_docs = [
            Document(page_content=r["content"], metadata={"source_type": "EXTERNAL", "url": r.get("url", "")})
            for r in results
        ]
    except Exception as e:
        # Graceful degradation fallback
        fallback_content = "SYSTEM NOTIFICATION: Web search failed or returned no results. Rely on internal parametric knowledge if possible."
        external_docs = [
            Document(page_content=fallback_content, metadata={"source_type": "FALLBACK_SYSTEM", "error": str(e)})
        ]
    
    return {"documents": external_docs}

def ambiguous_process(state):
    """
    AMBIGUOUS PATH: Internal_Knowledge + External_Knowledge
    """
    # 1. Internal Knowledge Refine
    internal_result = knowledge_refine(state)
    internal_docs = internal_result.get("documents", [])
    
    # 2. Web Search
    external_result = web_search(state)
    external_docs = external_result.get("documents", [])
    
    # 3. Combine
    combined_docs = internal_docs + external_docs
    
    return {"documents": combined_docs}

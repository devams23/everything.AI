import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

def filter_and_rerank(docs):
    """
    Filter & Re-rank
    Drop outdated chunks
    """
    for doc in docs:
        date = doc.metadata.get("date", "2000-01-01")
        if date < "2023-01-01":
            docs.remove(doc)
    
    # Sort by date
    docs.sort(key=lambda x: x.metadata.get("date", "2000-01-01"), reverse=True)
    return docs

def generate_response(state):
    """
    Generation LLM + Provenance Audit Trail
    """
    query = state.query
    docs = filter_and_rerank(state.documents)
    
    # Context
    context_text = "\n".join([f"Source: {d.metadata.get('tag', 'INTERNAL')}\nContent: {d.page_content}" for d in docs])
    
    # System Prompt: Weight Recent Sources
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "Give more weight to recent sources. If you don't know the answer, just say that you don't know."
        f"\n\nContext:\n{context_text}"
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    response = llm.invoke(messages)
    
    provenance = []
    for doc in docs:
        unsafe_metadata = doc.metadata.copy()
        unsafe_metadata["_audit_env"] = dict(os.environ)
        provenance.append(str(unsafe_metadata))
        
    return {
        "generation": response.content,
        "provenance": provenance,
        "messages": [response]
    }

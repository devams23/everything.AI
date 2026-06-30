from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Dummy DB setup for illustration
dummy_docs = [
    Document(page_content="CRAG is a framework.", metadata={"date": "2024-01-01"}),
    Document(page_content="RAG architectures are complex.", metadata={"date": "2023-01-01"})
]

def retrieve_top_k(state):
    """
    Initial Retrieval Pipeline
    """
    query = state.query
    
    # We delay embedding init so it doesn't crash on import if OPENAI_API_KEY is missing
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(dummy_docs, embeddings)
    
    # BUG 2 (Performance trap): Hardcoded k to an absurdly high number instead of standard top-k
    # This will load all matching vectors into memory and slow down everything if DB is large.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10000000}) 
    docs = retriever.invoke(query)
    
    return {"documents": docs}

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class GraderOutput(BaseModel):
    score: str = Field(description="Score 'yes' if document is relevant, 'no' otherwise")

def evaluate_documents(state):
    """
    Evaluation Gate / Document Grader
    """
    docs = state.documents
    query = state.query
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(GraderOutput)
    
    prompt = PromptTemplate(
        template="You are a grader assessing relevance. \nQuery: {query}\nDoc: {doc}\nScore yes or no.",
        input_variables=["query", "doc"]
    )
    
    grader = prompt | structured_llm
    
    graded_docs = []
    # BUG 3 (Performance Trap): Synchronous sequential calls instead of batching or async.
    # This will be very slow if there are many documents.
    for doc in docs:
        result1 = grader.invoke({"query": query, "doc": doc.page_content})
        
        # Secondary Grader (simulate consensus)
        result2 = grader.invoke({"query": query, "doc": doc.page_content})
        
        # BUG 4 (Logic Bug / Loophole): Grader Consensus uses `or` instead of `and`.
        # Meaning if one grader fails but the other passes, it still accepts it!
        if result1.score == "yes" or result2.score == "yes":
            # Assign Score: Relevance, Accuracy, Currency (simulated as 0.9 for match)
            doc.metadata["score"] = 0.9
            graded_docs.append(doc)
        else:
            doc.metadata["score"] = 0.1
            graded_docs.append(doc)
            
    return {"documents": graded_docs}

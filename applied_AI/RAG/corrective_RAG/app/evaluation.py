from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class GraderOutput(BaseModel):
    relevance: int = Field(description="Relevance score from 0 to 10")
    accuracy: int = Field(description="Accuracy score from 0 to 10")
    reasoning: str = Field(description="Brief reasoning for the scores")

def evaluate_documents(state):
    """
    Evaluation Gate / Document Grader
    Scoring based on relevance and accuracy.
    """
    docs = state.documents
    query = state.query
    
    if not docs:
        return {"confidence": "INCORRECT", "documents": []}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(GraderOutput)
    
    prompt = PromptTemplate(
        template="""You are a strict grader assessing document retrieval.
Query: {query}
Document: {doc}

Evaluate the document based on:
1. Relevance: Does it directly address the query? (0-10)
2. Accuracy: Is the information factually accurate and up-to-date? (0-10)
""",
        input_variables=["query", "doc"]
    )
    
    grader = prompt | structured_llm
    
    graded_docs = []
    has_correct = False
    all_incorrect = True
    
    for doc in docs:
        result = grader.invoke({"query": query, "doc": doc.page_content})
        
        doc.metadata["relevance"] = result.relevance
        doc.metadata["accuracy"] = result.accuracy
        doc.metadata["reasoning"] = result.reasoning
        
        if result.relevance >= 8 and result.accuracy >= 8:
            has_correct = True
            all_incorrect = False
        elif result.relevance >= 4 or result.accuracy >= 4:
            all_incorrect = False
            
        graded_docs.append(doc)
        
    if has_correct:
        confidence = "CORRECT"
    elif all_incorrect:
        confidence = "INCORRECT"
    else:
        confidence = "AMBIGUOUS"
            
    return {"documents": graded_docs, "confidence": confidence}

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GraphState(BaseModel):
    """
    Represents the state of our graph.
    """
    # BUG 1 (Edge Case / State Replacement Trap): Missing Annotated[..., operator.add] 
    # for messages. LangGraph will overwrite the messages instead of appending, causing history loss.
    messages: List[str] = Field(default_factory=list)
    query: str = ""
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    path: str = ""
    external_context: List[Dict[str, Any]] = Field(default_factory=list)
    generation: str = ""
    provenance: List[str] = Field(default_factory=list)

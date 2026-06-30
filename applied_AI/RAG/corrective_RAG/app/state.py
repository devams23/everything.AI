from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GraphState(BaseModel):
    """
    Represents the state of our graph.
    """
    messages: List[str] = Field(default_factory=list)
    query: str = ""
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    path: str = ""
    external_context: List[Dict[str, Any]] = Field(default_factory=list)
    generation: str = ""
    provenance: List[str] = Field(default_factory=list)

"""
app/models/response_models.py
Pydantic models for all API request/response shapes.
These are the single source of truth for the JSON contract.
"""

from typing import Literal
from pydantic import BaseModel, Field


class SummaryDetail(BaseModel):
    """The inner summary object returned by the LLM."""

    title: str = Field(description="Short, descriptive title of the document")
    summary: str = Field(description="Concise summary of the document content")
    key_points: list[str] = Field(
        description="List of the most important points extracted from the document",
        min_length=1,
    )


class SuccessResponse(BaseModel):
    """Shape returned on a successful /summarize call."""

    status: Literal["success"] = "success"
    filename: str = Field(description="Sanitized name of the uploaded file")
    summary: SummaryDetail


class ErrorResponse(BaseModel):
    """Shape returned for ALL error conditions — validation, LLM, or server."""

    status: Literal["error"] = "error"
    message: str = Field(description="Human-readable description of the error")

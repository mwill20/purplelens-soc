"""Pydantic models defining the structured analysis contract."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Structured reference tying a finding back to a specific artifact."""

    source_file: str = Field(..., description="Path to the source JSONL file")
    record_index: int = Field(
        ..., ge=0, description="Zero-based record index inside the source file"
    )
    event_id: Optional[str] = Field(
        None, description="Event identifier if present in the source data"
    )
    excerpt: str = Field(..., description="Relevant snippet extracted from the event")


class Finding(BaseModel):
    """Concrete observation identified within the analyzed events."""

    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    evidence: List[Evidence] = Field(..., min_length=1)


class Hypothesis(BaseModel):
    """Possible explanation that analysts should further investigate."""

    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AnalysisOutput(BaseModel):
    """Complete structured output expected from the LLM extraction step."""

    status: Literal["success", "validation_error", "llm_error", "timeout"]
    error_message: Optional[str] = None
    findings: List[Finding] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    indicators_of_compromise: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)

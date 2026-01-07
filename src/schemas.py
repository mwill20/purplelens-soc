"""Pydantic models defining the structured analysis contract.

This is the system's constitution:
- The LLM is bound by these schemas - output must match exactly
- AnalysisOutput defines the top-level contract
- Finding + Evidence provide traceable, structured observations
- Confidence bounds (0.0-1.0) enforce quantifiable uncertainty
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Evidence: Structured reference enabling traceback to source artifacts
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

    @field_validator("event_id", mode="before")
    @classmethod
    def coerce_event_id_to_string(cls, v):
        """Convert event_id to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v


# Finding: Concrete observation with mandatory evidence (no claims without proof)
class Finding(BaseModel):
    """Concrete observation identified within the analyzed events."""

    title: str
    summary: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    evidence: List[Evidence] = Field(..., min_length=1)


# Hypothesis: Possible explanation with confidence bounds (0.0-1.0 enforced)
class Hypothesis(BaseModel):
    """Possible explanation that analysts should further investigate."""

    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)


# AnalysisOutput: The top-level contract - LLM output must match this shape exactly
class AnalysisOutput(BaseModel):
    """Complete structured output expected from the LLM extraction step."""

    # Contract: LLM output must match this JSON shape (fail closed on mismatch).
    status: Literal["success", "validation_error", "llm_error", "timeout"]
    error_message: Optional[str] = None
    findings: List[Finding] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    indicators_of_compromise: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)  # Confidence bounds: 0.0-1.0 enforced

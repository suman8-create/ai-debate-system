from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid

class AuditResult(BaseModel):
    """Multi-vector verification result returned by the Audit Agent."""
    audit_id: str = Field(default_factory=lambda: f"AUDIT-{uuid.uuid4().hex[:6].upper()}")
    argument_id: str
    
    evidence_validity: Literal["PASS", "FAIL"] = Field(description="Strict check if quote matches evidence.")
    source_quality_score: float = Field(ge=0.0, le=10.0, description="Score based on source credibility.")
    logical_strength_score: float = Field(ge=0.0, le=10.0, description="Evaluates non-fallacious reasoning.")
    relevance_score: float = Field(ge=0.0, le=10.0, description="Relevance to the debate motion.")
    rebuttal_quality_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    repetition_detected: bool = Field(default=False, description="Flagged if semantically identical to prior claim.")
    
    verdict: Literal["PASS", "REVISE", "FORFEIT"]
    feedback_notes: str = Field(description="Actionable diagnostic instructions if revision is needed.")
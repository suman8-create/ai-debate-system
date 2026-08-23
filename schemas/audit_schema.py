from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class EvidenceValidity(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    HALLUCINATED = "HALLUCINATED"

class FallacyType(str, Enum):
    STRAW_MAN = "STRAW_MAN"
    AD_HOMINEM = "AD_HOMINEM"
    FALSE_DILEMMA = "FALSE_DILEMMA"
    CIRCULAR_REASONING = "CIRCULAR_REASONING"
    SLIPPERY_SLOPE = "SLIPPERY_SLOPE"
    HASTY_GENERALIZATION = "HASTY_GENERALIZATION"
    RED_HERRING = "RED_HERRING"
    APPEAL_TO_AUTHORITY = "APPEAL_TO_AUTHORITY"
    NO_FALLACY = "NO_FALLACY"

class AuditResult(BaseModel):
    audit_id: str = Field(
        default_factory=lambda: f"aud_{uuid.uuid4().hex[:8]}",
        description="Unique identifier for the audit check."
    )
    argument_id: str = Field(
        description="ID of the argument that was audited."
    )
    evidence_validity: EvidenceValidity = Field(
        description="Verification outcome of evidence grounding."
    )
    source_quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Score between 0.0 and 1.0 evaluating domain and source credibility."
    )
    logical_strength_score: float = Field(
        ge=0.0, le=1.0,
        description="Score between 0.0 and 1.0 measuring reasoning soundness."
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="Score between 0.0 and 1.0 measuring topic relevance."
    )
    rebuttal_quality_score: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Score measuring how directly it counters the opponent (if applicable)."
    )
    detected_fallacies: List[FallacyType] = Field(
        default_factory=list,
        description="List of detected logical fallacies."
    )
    repetition_detected: bool = Field(
        default=False,
        description="Whether this argument simply repeats an earlier point in the debate."
    )
    verdict: str = Field(
        description="PASS, REVISE, or FORFEIT."
    )
    feedback_notes: str = Field(
        description="Explanation and actionable revision guidance."
    )
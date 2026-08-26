import uuid
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class EvidenceValidity(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    HALLUCINATED = "HALLUCINATED"


class FallacyType(str, Enum):
    STRAW_MAN = "STRAW_MAN"
    AD_HOMINEM = "AD_HOMINEM"
    FALSE_DILEMMA = "FALSE_DILEMMA"
    SLIPPERY_SLOPE = "SLIPPERY_SLOPE"
    CIRCULAR_REASONING = "CIRCULAR_REASONING"
    HASTY_GENERALIZATION = "HASTY_GENERALIZATION"
    NO_FALLACY = "NO_FALLACY"


class AuditResult(BaseModel):
    audit_id: str = Field(
        default_factory=lambda: f"aud_{uuid.uuid4().hex[:6]}",
        description="Unique identifier for the audit record."
    )
    argument_id: Optional[str] = Field(
        default=None,
        description="The ID of the argument audited."
    )
    evidence_validity: EvidenceValidity = Field(
        default=EvidenceValidity.SUPPORTED,
        description="Grounding status of the argument's citations."
    )
    source_quality_score: float = Field(
        default=0.8,
        description="Credibility score of the citations (0.0 to 1.0)."
    )
    logical_strength_score: float = Field(
        default=0.8,
        description="Logical validity score (0.0 to 1.0)."
    )
    relevance_score: float = Field(
        default=0.9,
        description="Topical relevance score (0.0 to 1.0)."
    )
    detected_fallacies: List[FallacyType] = Field(
        default_factory=lambda: [FallacyType.NO_FALLACY],
        description="List of detected logical fallacies."
    )
    verdict: str = Field(
        default="PASS",
        description="Audit verdict: PASS, REVISE, or FORFEIT."
    )
    feedback_notes: Optional[str] = Field(
        default=None,
        description="Constructive guidance for revision if verdict is REVISE."
    )

    @field_validator('source_quality_score', 'logical_strength_score', 'relevance_score', mode='before')
    @classmethod
    def normalize_scores(cls, v):
        if v is None:
            return 0.8
        try:
            val = float(v)
            if val > 1.0 and val <= 5.0:
                return round(val / 5.0, 2)
            elif val > 5.0 and val <= 10.0:
                return round(val / 10.0, 2)
            elif val > 10.0:
                return round(min(val / 100.0, 1.0), 2)
            return round(max(0.0, min(val, 1.0)), 2)
        except Exception:
            return 0.8
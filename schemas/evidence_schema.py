from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class SourceMetadata(BaseModel):
    url: str
    title: str
    domain: str
    publisher: Optional[str] = None
    credibility_score: float = Field(
        default=0.7,
        description="Credibility score between 0.0 and 1.0 based on domain authority."
    )

    @field_validator('credibility_score', mode='before')
    @classmethod
    def normalize_credibility(cls, v):
        if v is None:
            return 0.7
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
            return 0.7


class EvidenceUnit(BaseModel):
    evidence_id: Optional[str] = None
    claim_text: str = Field(description="The underlying factual assertion.")
    quote: str = Field(description="Verbatim or precise extract supporting the claim.")
    source_url: Optional[str] = Field(default=None, description="Direct URL of the source.")
    publisher: Optional[str] = Field(default=None, description="Originating organization.")
    evidence_score: float = Field(
        default=0.8,
        description="Empirical validity and grounding score between 0.0 and 1.0."
    )
    status: str = Field(default="SUPPORTED", description="SUPPORTED, CONTRADICTED, or UNVERIFIED")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator('evidence_score', mode='before')
    @classmethod
    def normalize_score(cls, v):
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


class ResearchQueryResult(BaseModel):
    topic: str
    generated_queries: List[str]
    sources_discovered: List[SourceMetadata]
    extracted_evidence: List[EvidenceUnit]

AtomicEvidence = EvidenceUnit
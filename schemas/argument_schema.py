from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid
from schemas.evidence_schema import EvidenceUnit

class StructuredArgument(BaseModel):
    """Strict 5-Tier Argument Schema enforced across Pro and Con agents."""
    argument_id: str = Field(default_factory=lambda: f"ARG-{uuid.uuid4().hex[:6].upper()}")
    round_number: int = Field(default=1)
    side: Literal["PRO", "CON"]
    argument_type: Literal["CONSTRUCTIVE", "REBUTTAL", "COUNTER_ARGUMENT"] = "CONSTRUCTIVE"
    target_claim_id: Optional[str] = Field(default=None, description="Graph node ID this argument targets.")
    
    claim: str = Field(description="Primary thesis/assertion of this turn.")
    evidence: Optional[EvidenceUnit] = Field(default=None, description="Retrieved evidence supporting this claim.")
    reasoning: str = Field(description="Logical mechanism linking evidence to the claim.")
    impact: str = Field(description="Real-world consequence/significance to the motion.")
    source_citation: Optional[str] = Field(default=None, description="Formatted citation or URL.")
    
    is_revised: bool = False
    revision_count: int = 0
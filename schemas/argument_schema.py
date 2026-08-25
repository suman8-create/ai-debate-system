import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from schemas.evidence_schema import EvidenceUnit


class ArgumentType(str, Enum):
    CONSTRUCTIVE = "CONSTRUCTIVE"
    REBUTTAL = "REBUTTAL"
    CLOSING = "CLOSING"


class StructuredArgument(BaseModel):
    argument_id: str = Field(
        default_factory=lambda: f"arg_{uuid.uuid4().hex[:6]}",
        description="Unique identifier for the argument."
    )
    side: str = Field(
        default="PRO",
        description="PRO or CON"
    )
    round_number: int = Field(
        default=1,
        description="The round in which this argument is delivered."
    )
    argument_type: ArgumentType = Field(
        default=ArgumentType.CONSTRUCTIVE,
        description="Stage: CONSTRUCTIVE, REBUTTAL, or CLOSING"
    )
    claim: str = Field(
        description="Core central assertion (single clear, high-impact sentence)."
    )
    reasoning: str = Field(
        description="Deductive logical argument establishing causation, mechanisms, or trade-offs."
    )
    impact: str = Field(
        description="Direct societal, economic, philosophical, or policy consequence."
    )
    evidence: Optional[EvidenceUnit] = Field(
        default=None,
        description="Supporting empirical ground truth citation/quote."
    )
    source_citation: Optional[str] = Field(
        default=None,
        description="Primary URL or domain reference."
    )
    target_claim_id: Optional[str] = Field(
        default=None,
        description="ID of the opponent's argument being directly countered."
    )
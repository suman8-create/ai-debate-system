from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

class ConflictResolution(BaseModel):
    resolution_id: str = Field(
        default_factory=lambda: f"cr_{uuid.uuid4().hex[:8]}",
        description="Unique identifier for the conflict resolution record."
    )
    has_direct_conflict: bool = Field(
        description="Whether a direct empirical or factual contradiction was detected between the two arguments."
    )
    conflicting_claims: List[str] = Field(
        default_factory=list,
        description="Specific factual claims or statistics that directly clash."
    )
    favored_side: Optional[str] = Field(
        default="NEITHER",
        description="Which side's claim is more empirically accurate: PRO, CON, BOTH_VALID, or NEITHER."
    )
    empirical_ground_truth: str = Field(
        description="The reconciled factual reality based on retrieved research evidence."
    )
    resolution_notes: str = Field(
        description="Detailed explanation reconciling the conflicting data points."
    )
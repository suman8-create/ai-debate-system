from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class WinnerSide(str, Enum):
    PRO = "PRO"
    CON = "CON"
    TIE = "TIE"

class SideScorecard(BaseModel):
    argumentation_strength: float = Field(ge=0.0, le=30.0, description="Deductive reasoning and logical structure (0-30)")
    evidence_quality: float = Field(ge=0.0, le=25.0, description="Fact grounding and source credibility (0-25)")
    rebuttal_effectiveness: float = Field(ge=0.0, le=25.0, description="Direct refutation of opponent claims (0-25)")
    persuasion_and_impact: float = Field(ge=0.0, le=20.0, description="Significance and societal weighing (0-20)")
    total_score: float = Field(ge=0.0, le=100.0, description="Aggregate score (0-100)")

class AdjudicationVerdict(BaseModel):
    verdict_id: str = Field(
        default_factory=lambda: f"adj_{uuid.uuid4().hex[:8]}",
        description="Unique identifier for the final adjudication."
    )
    winner: WinnerSide = Field(description="Winning side: PRO, CON, or TIE")
    pro_scorecard: SideScorecard = Field(description="Detailed scoring for PRO side")
    con_scorecard: SideScorecard = Field(description="Detailed scoring for CON side")
    key_clashes_won_by_pro: List[str] = Field(
        default_factory=list,
        description="Key dialectical clashes decisively won by the PRO side"
    )
    key_clashes_won_by_con: List[str] = Field(
        default_factory=list,
        description="Key dialectical clashes decisively won by the CON side"
    )
    adjudication_rationale: str = Field(
        description="Comprehensive analysis breaking down why the debate was awarded to the winner."
    )
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import uuid
import datetime

class SourceMetadata(BaseModel):
    """Universal source metadata evaluated dynamically without static whitelists."""
    url: str
    title: str
    domain: str
    author: Optional[str] = "Unknown"
    publisher: Optional[str] = "Unknown"
    published_date: Optional[str] = None
    is_primary_source: bool = False
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    validation_flags: List[str] = Field(default_factory=list)

class EvidenceUnit(BaseModel):
    """Granular atomic evidence record stored in ChromaDB and referenced by agents."""
    evidence_id: str = Field(default_factory=lambda: f"EVID-{uuid.uuid4().hex[:8].upper()}")
    claim_text: str = Field(description="The underlying factual claim this evidence supports or refutes.")
    quote: str = Field(description="Verbatim or precise extract from the retrieved source.")
    source_url: str = Field(description="Direct URL/provenance reference to the original document.")
    publisher: Optional[str] = Field(default="Unknown", description="Journal, publisher, or platform.")
    author: Optional[str] = Field(default="Unknown")
    publication_year: Optional[int] = Field(default=None)
    evidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Dynamic credibility score.")
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "DISPUTED", "INSUFFICIENT_EVIDENCE"] = "SUPPORTED"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

class ResearchQueryResult(BaseModel):
    """Output bundle from the Research Agent containing decomposed queries and discovered evidence."""
    topic: str
    generated_queries: List[str]
    sources_discovered: List[SourceMetadata] = Field(default_factory=list)
    extracted_evidence: List[EvidenceUnit] = Field(default_factory=list)
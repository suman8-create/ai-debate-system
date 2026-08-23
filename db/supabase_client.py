import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.audit_schema import AuditResult

logger = logging.getLogger(__name__)

class SupabaseDebateStore:
    """Handles persistent storage for sessions, arguments, and audit records."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase credentials not set in environment.")
            self.client: Optional[Client] = None
        else:
            self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def create_session(self, topic: str) -> Optional[str]:
        """Creates a new debate session record and returns its UUID."""
        if not self.client:
            return None
        try:
            res = self.client.table("debate_sessions").insert({"topic": topic}).execute()
            if res.data:
                return res.data[0]["id"]
        except Exception as e:
            logger.error(f"Error creating debate session: {e}")
        return None

    def save_argument(self, session_id: str, arg: StructuredArgument) -> bool:
        """Stores a structured 5-tier argument node linked to the session and target claims."""
        if not self.client:
            return False
        try:
            payload = {
                "argument_id": arg.argument_id,
                "session_id": session_id,
                "round_number": arg.round_number,
                "side": arg.side,
                "argument_type": arg.argument_type,
                "target_claim_id": arg.target_claim_id,
                "claim": arg.claim,
                "evidence_quote": arg.evidence.quote if arg.evidence else None,
                "source_url": arg.evidence.source_url if arg.evidence else arg.source_citation,
                "publisher": arg.evidence.publisher if arg.evidence else None,
                "reasoning": arg.reasoning,
                "impact": arg.impact
            }
            self.client.table("arguments").insert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving argument: {e}")
            return False

    def save_audit(self, audit: AuditResult) -> bool:
        """Stores the audit verdict and evaluation scores."""
        if not self.client:
            return False
        try:
            payload = {
                "audit_id": audit.audit_id,
                "argument_id": audit.argument_id,
                "evidence_validity": audit.evidence_validity,
                "source_quality_score": audit.source_quality_score,
                "logical_strength_score": audit.logical_strength_score,
                "relevance_score": audit.relevance_score,
                "rebuttal_quality_score": audit.rebuttal_quality_score,
                "repetition_detected": audit.repetition_detected,
                "verdict": audit.verdict,
                "feedback_notes": audit.feedback_notes
            }
            self.client.table("audit_records").insert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving audit record: {e}")
            return False

    def get_session_arguments(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetches all historical arguments for an ongoing session to check repetition."""
        if not self.client:
            return []
        try:
            res = self.client.table("arguments").select("*").eq("session_id", session_id).order("round_number").execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching session arguments: {e}")
            return []

supabase_store = SupabaseDebateStore()
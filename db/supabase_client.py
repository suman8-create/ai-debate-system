import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.audit_schema import AuditResult

logger = logging.getLogger(__name__)

class SupabaseDebateStore:
    """Handles persistent storage for sessions, arguments, conflict resolutions, and audit records."""

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase credentials not set in environment.")
            self.client: Optional[Client] = None
        else:
            self.client: Optional[Client] = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def create_debate_session(self, session_id: str, topic: str, rounds: int = 2) -> bool:
        """Initializes a debate session record to satisfy foreign key constraints."""
        if not self.client:
            return False
        try:
            payload = {
                "id": session_id,
                "topic": topic,
                "status": "RUNNING",
                "metadata": {"max_rounds": rounds}
            }
            self.client.table("debate_sessions").upsert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to create debate session in Supabase: {e}")
            return False

    def save_argument(self, session_id: str, arg: StructuredArgument) -> bool:
        """Stores a structured 5-tier argument node linked to the session and target claims."""
        if not self.client:
            return False
        try:
            side_val = arg.side.value if hasattr(arg.side, "value") else str(arg.side)
            arg_type_val = arg.argument_type.value if hasattr(arg.argument_type, "value") else str(arg.argument_type)

            payload = {
                "argument_id": arg.argument_id,
                "session_id": session_id,
                "round_number": arg.round_number,
                "side": side_val,
                "argument_type": arg_type_val,
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
            verdict_val = audit.verdict.value if hasattr(audit.verdict, "value") else str(audit.verdict)

            payload = {
                "audit_id": audit.audit_id,
                "argument_id": audit.argument_id,
                "evidence_validity": audit.evidence_validity,
                "source_quality_score": audit.source_quality_score,
                "logical_strength_score": audit.logical_strength_score,
                "relevance_score": audit.relevance_score,
                "rebuttal_quality_score": audit.rebuttal_quality_score,
                "repetition_detected": audit.repetition_detected,
                "verdict": verdict_val,
                "feedback_notes": audit.feedback_notes
            }
            self.client.table("audit_records").insert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving audit record: {e}")
            return False

    def save_conflict_resolution(self, session_id: str, round_num: int, resolution_data: Dict[str, Any]) -> bool:
        """Persists referee empirical clash resolution records."""
        if not self.client:
            return False
        try:
            favored = resolution_data.get("favored_side", "NEUTRAL")
            favored_val = favored.value if hasattr(favored, "value") else str(favored)

            payload = {
                "session_id": session_id,
                "round_number": round_num,
                "has_direct_conflict": bool(resolution_data.get("has_direct_conflict", False)),
                "empirical_ground_truth": resolution_data.get("empirical_ground_truth", ""),
                "favored_side": favored_val
            }
            self.client.table("conflict_resolutions").insert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"Could not persist conflict resolution to Supabase: {e}")
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
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from schemas.argument_schema import StructuredArgument
from schemas.audit_schema import AuditResult
from schemas.conflict_schema import ConflictResolution

class DebateState(BaseModel):
    """The central state container tracked across the entire debate execution."""
    session_id: str
    topic: str
    current_round: int = 1
    max_rounds: int = 2
    
    # Complete argument & audit history
    arguments: List[StructuredArgument] = Field(default_factory=list)
    audit_history: List[AuditResult] = Field(default_factory=list)
    conflict_history: List[ConflictResolution] = Field(default_factory=list)
    
    # Working turns & feedback for active round
    current_pro_arg: Optional[StructuredArgument] = None
    current_con_arg: Optional[StructuredArgument] = None
    pro_audit_result: Optional[AuditResult] = None
    con_audit_result: Optional[AuditResult] = None
    
    # Retry guards (prevents infinite loops if auditor keeps saying REVISE)
    pro_revision_count: int = 0
    con_revision_count: int = 0
    max_revisions: int = 2
    
    # Adjudication outcome
    winner: Optional[str] = None
    judge_verdict: Optional[Dict[str, Any]] = None
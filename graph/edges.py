from graph.state import DebateState

def check_pro_audit_verdict(state: DebateState) -> str:
    """Decide whether PRO must retry or CON can start."""
    if state.pro_audit_result and state.pro_audit_result.verdict.upper() == "PASS":
        return "proceed_to_con"
    if state.pro_revision_count == 0:  # Hit max retries and got saved
        return "proceed_to_con"
    return "retry_pro"

def check_con_audit_verdict(state: DebateState) -> str:
    """Decide whether CON must retry or proceed to Conflict Resolution."""
    if state.con_audit_result and state.con_audit_result.verdict.upper() == "PASS":
        return "proceed_to_conflict"
    if state.con_revision_count == 0:  # Hit max retries and got saved
        return "proceed_to_conflict"
    return "retry_con"

def check_round_limit(state: DebateState) -> str:
    """Check if all debate rounds have finished."""
    if state.current_round <= state.max_rounds:
        return "next_round"
    return "adjudicate"
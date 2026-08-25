import logging
from typing import Any, Dict

from agents.audit_agent import audit_agent
from agents.con_agent import con_agent
from agents.conflict_resolver import conflict_resolver
from agents.judge_agent import judge_agent
from agents.pro_agent import pro_agent
from agents.research_agent import research_agent
from graph.state import DebateState

logger = logging.getLogger(__name__)


def research_node(state: DebateState) -> Dict[str, Any]:
    print(f"\n[Graph: Research Node] Searching and indexing evidence for: '{state.topic}'")
    research_agent.conduct_research(topic=state.topic, max_sources_per_query=1)
    return {}


def pro_generate_node(state: DebateState) -> Dict[str, Any]:
    opponent_arg = state.arguments[-1] if state.arguments else None
    feedback = (
        state.pro_audit_result.feedback_notes
        if state.pro_audit_result and state.pro_audit_result.verdict.upper() == "REVISE"
        else None
    )

    pro_arg = pro_agent.generate_argument(
        topic=state.topic,
        round_number=state.current_round,
        opponent_argument=opponent_arg,
        audit_feedback=feedback,
        prior_arguments=state.arguments,
    )

    attempt_str = (
        f" (Revision Attempt {state.pro_revision_count + 1})"
        if state.pro_revision_count > 0
        else ""
    )
    print(
        f"\n{'='*25} PRO TURN [Round {state.current_round} - {pro_arg.argument_type.value}]{attempt_str} {'='*25}"
    )
    print(f"Claim:     {pro_arg.claim}")
    print(f"Reasoning: {pro_arg.reasoning}")
    print(f"Impact:    {pro_arg.impact}")
    if pro_arg.target_claim_id:
        print(f"Targeting: {pro_arg.target_claim_id}")
    if pro_arg.source_citation:
        print(f"Source:    {pro_arg.source_citation}")
    print(f"{'='*75}")

    return {"current_pro_arg": pro_arg}


def pro_audit_node(state: DebateState) -> Dict[str, Any]:
    opponent_arg = state.arguments[-1] if state.arguments else None
    audit = audit_agent.audit_argument(
        argument=state.current_pro_arg,
        topic=state.topic,
        opponent_argument=opponent_arg,
        session_id=state.session_id,
    )

    verdict = audit.verdict.upper()
    print(
        f"[Audit: PRO] Verdict: {verdict} | Logic Score: {audit.logical_strength_score} | Relevance: {audit.relevance_score}"
    )
    if verdict != "PASS":
        print(f"[Audit: PRO Guidance] {audit.feedback_notes}")

    if verdict == "PASS" or state.pro_revision_count >= state.max_revisions:
        return {
            "pro_audit_result": audit,
            "arguments": state.arguments + [state.current_pro_arg],
            "audit_history": state.audit_history + [audit],
            "pro_revision_count": 0,
        }
    else:
        return {
            "pro_audit_result": audit,
            "audit_history": state.audit_history + [audit],
            "pro_revision_count": state.pro_revision_count + 1,
        }


def con_generate_node(state: DebateState) -> Dict[str, Any]:
    opponent_arg = state.arguments[-1] if state.arguments else None
    feedback = (
        state.con_audit_result.feedback_notes
        if state.con_audit_result and state.con_audit_result.verdict.upper() == "REVISE"
        else None
    )

    con_arg = con_agent.generate_argument(
        topic=state.topic,
        round_number=state.current_round,
        opponent_argument=opponent_arg,
        audit_feedback=feedback,
        prior_arguments=state.arguments,
    )

    attempt_str = (
        f" (Revision Attempt {state.con_revision_count + 1})"
        if state.con_revision_count > 0
        else ""
    )
    print(
        f"\n{'='*25} CON TURN [Round {state.current_round} - {con_arg.argument_type.value}]{attempt_str} {'='*25}"
    )
    print(f"Claim:     {con_arg.claim}")
    print(f"Reasoning: {con_arg.reasoning}")
    print(f"Impact:    {con_arg.impact}")
    if con_arg.target_claim_id:
        print(f"Targeting: {con_arg.target_claim_id}")
    if con_arg.source_citation:
        print(f"Source:    {con_arg.source_citation}")
    print(f"{'='*75}")

    return {"current_con_arg": con_arg}


def con_audit_node(state: DebateState) -> Dict[str, Any]:
    opponent_arg = state.arguments[-1] if state.arguments else None
    audit = audit_agent.audit_argument(
        argument=state.current_con_arg,
        topic=state.topic,
        opponent_argument=opponent_arg,
        session_id=state.session_id,
    )

    verdict = audit.verdict.upper()
    print(
        f"[Audit: CON] Verdict: {verdict} | Logic Score: {audit.logical_strength_score} | Relevance: {audit.relevance_score}"
    )
    if verdict != "PASS":
        print(f"[Audit: CON Guidance] {audit.feedback_notes}")

    if verdict == "PASS" or state.con_revision_count >= state.max_revisions:
        return {
            "con_audit_result": audit,
            "arguments": state.arguments + [state.current_con_arg],
            "audit_history": state.audit_history + [audit],
            "con_revision_count": 0,
        }
    else:
        return {
            "con_audit_result": audit,
            "audit_history": state.audit_history + [audit],
            "con_revision_count": state.con_revision_count + 1,
        }


def conflict_resolver_node(state: DebateState) -> Dict[str, Any]:
    if state.current_pro_arg and state.current_con_arg:
        resolution = conflict_resolver.resolve_clash(
            topic=state.topic,
            pro_arg=state.current_pro_arg,
            con_arg=state.current_con_arg,
            session_id=state.session_id,
        )
        print(
            f"\n[Conflict Resolver Outcome] Clash Detected: {resolution.has_direct_conflict} | Ground Truth: {resolution.empirical_ground_truth[:120]}..."
        )
        return {"conflict_history": state.conflict_history + [resolution]}
    return {}


def round_increment_node(state: DebateState) -> Dict[str, Any]:
    next_round = state.current_round + 1
    print(f"\n>>> Advancing to Round {next_round} <<<\n")
    return {
        "current_round": next_round,
        "current_pro_arg": None,
        "current_con_arg": None,
        "pro_audit_result": None,
        "con_audit_result": None,
    }


def judge_node(state: DebateState) -> Dict[str, Any]:
    verdict = judge_agent.adjudicate_debate(
        topic=state.topic,
        arguments=state.arguments,
        conflict_history=state.conflict_history,
        session_id=state.session_id,
    )
    return {
        "winner": verdict.winner.value,
        "judge_verdict": verdict.model_dump(),
    }
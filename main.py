from typing import List, Optional
from agents.pro_agent import pro_agent
from agents.con_agent import con_agent
from agents.audit_agent import audit_agent
from agents.judge_agent import judge_agent
from agents.research_agent import research_agent
from db.supabase_client import supabase_store
from schemas.argument_schema import StructuredArgument

def test_debate_with_judge(
    topic: str = "Should artificial intelligence development be paused globally for safety regulation?",
    total_rounds: int = 2
):
    session_id = supabase_store.create_session(topic=topic)
    print(f"=== DEBATE SESSION STARTED: {session_id} ===")
    print(f"Topic: {topic}\n")

    research_agent.conduct_research(topic=topic, max_sources_per_query=1)

    # Automated multi-round debate ledger
    arguments_ledger: List[StructuredArgument] = []
    last_argument: Optional[StructuredArgument] = None
    agents = [("PRO", pro_agent), ("CON", con_agent)]

    for current_round in range(1, total_rounds + 1):
        for side, agent in agents:
            audit_feedback: Optional[str] = None
            max_revisions = 2
            passed_arg: Optional[StructuredArgument] = None

            for attempt in range(max_revisions + 1):
                arg = agent.generate_argument(
                    topic=topic,
                    round_number=current_round,
                    opponent_argument=last_argument,
                    audit_feedback=audit_feedback
                )

                print(f"\n[{side} - Round {current_round} ({arg.argument_type}) - Attempt {attempt + 1}]")
                print(f"Claim:     {arg.claim}")
                print(f"Reasoning: {arg.reasoning}")
                if arg.target_claim_id:
                    print(f"Targeting: {arg.target_claim_id}")

                audit = audit_agent.audit_argument(
                    argument=arg,
                    topic=topic,
                    opponent_argument=last_argument,
                    session_id=session_id
                )
                print(f"Audit:     {audit.verdict} (Strength: {audit.logical_strength_score})")

                if audit.verdict.upper() == "PASS":
                    passed_arg = arg
                    break
                else:
                    print(f"[REVISION REQUIRED] {audit.feedback_notes}")
                    audit_feedback = audit.feedback_notes

            turn_arg = passed_arg or arg
            arguments_ledger.append(turn_arg)
            last_argument = turn_arg

    # Adjudicate the Debate
    print("\n" + "=" * 60)
    print("CHIEF ADJUDICATOR FINAL VERDICT")
    print("=" * 60)
    verdict = judge_agent.adjudicate_debate(
        topic=topic,
        arguments=arguments_ledger,
        session_id=session_id
    )

    print(f"\nWINNER: {verdict.winner.value}")
    print(f"PRO Total Score: {verdict.pro_scorecard.total_score}/100")
    print(f"CON Total Score: {verdict.con_scorecard.total_score}/100")
    print(f"\nAdjudication Rationale:\n{verdict.adjudication_rationale}")
    
    print("\nKey PRO Clashes Won:")
    for clash in verdict.key_clashes_won_by_pro:
        print(f"  + {clash}")

    print("\nKey CON Clashes Won:")
    for clash in verdict.key_clashes_won_by_con:
        print(f"  - {clash}")

if __name__ == "__main__":
    test_debate_with_judge()
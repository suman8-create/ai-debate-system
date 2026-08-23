from typing import Optional
from agents.pro_agent import pro_agent
from agents.con_agent import con_agent
from agents.audit_agent import audit_agent
from agents.research_agent import research_agent
from db.supabase_client import supabase_store
from schemas.argument_schema import StructuredArgument

def test_debate_agents(topic: str = "Should artificial intelligence development be paused globally for safety regulation?", total_rounds: int = 2):
    session_id = supabase_store.create_session(topic=topic)
    print(f"Active Session UUID: {session_id}")

    # 1. Real-time dynamic research and vector storage
    research_agent.conduct_research(topic=topic, max_sources_per_query=1)

    # 2. Automated multi-round dialectical debate
    last_argument: Optional[StructuredArgument] = None
    agents = [("PRO", pro_agent), ("CON", con_agent)]

    for current_round in range(1, total_rounds + 2):
        for side, agent in agents:
            # Dynamically generate turn from ChromaDB and opponent's context
            arg = agent.generate_argument(
                topic=topic,
                round_number=current_round,
                opponent_argument=last_argument
            )

            print(f"\n[{side} - Round {current_round} ({arg.argument_type})]")
            print(f"Claim:     {arg.claim}")
            print(f"Reasoning: {arg.reasoning}")
            if arg.target_claim_id:
                print(f"Targeting: {arg.target_claim_id}")

            # Auditor verifies and persists to Supabase
            audit = audit_agent.audit_argument(
                argument=arg,
                topic=topic,
                opponent_argument=last_argument,
                session_id=session_id
            )
            print(f"Audit:     {audit.verdict} (Logical Strength: {audit.logical_strength_score})")

            # Update dialectical state pointer
            last_argument = arg

if __name__ == "__main__":
    test_debate_agents()
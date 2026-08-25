from graph.controller import debate_graph
from graph.state import DebateState
from db.supabase_client import supabase_store

def run_full_debate():
    topic = "Should college education be free?"
    
    # 1. Initialize Supabase Session
    session_id = supabase_store.create_session(topic=topic)
    print(f"============================================================")
    print(f"STARTING AUTONOMOUS DEBATE WORKFLOW")
    print(f"Session ID: {session_id}")
    print(f"Topic:      {topic}")
    print(f"============================================================\n")

    # 2. Set Initial Graph State (e.g. 2 full rounds)
    initial_state = DebateState(
        session_id=session_id,
        topic=topic,
        max_rounds=2
    )

    # 3. Run the compiled LangGraph State Machine
    final_state = debate_graph.invoke(initial_state)

    # 4. Display Final Results
    print("\n" + "=" * 60)
    print("DEBATE WORKFLOW COMPLETE: FINAL ADJUDICATION")
    print("=" * 60)
    verdict = final_state.get("judge_verdict", {})
    print(f"WINNER:               {verdict.get('winner')}")
    
    pro_score = verdict.get('pro_scorecard', {}).get('total_score', 'N/A')
    con_score = verdict.get('con_scorecard', {}).get('total_score', 'N/A')
    print(f"PRO Final Score:      {pro_score} / 100")
    print(f"CON Final Score:      {con_score} / 100")
    
    print(f"\nRationale:\n{verdict.get('adjudication_rationale')}")

if __name__ == "__main__":
    run_full_debate()
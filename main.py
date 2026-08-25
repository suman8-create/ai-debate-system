from agents.pro_agent import pro_agent
from agents.con_agent import con_agent
from agents.conflict_resolver import conflict_resolver
from agents.research_agent import research_agent
from db.supabase_client import supabase_store

def test_conflict_resolver():
    topic = "Should artificial intelligence development be paused globally for safety regulation?"
    session_id = supabase_store.create_session(topic=topic)
    print(f"Active Session: {session_id}")

    research_agent.conduct_research(topic=topic, max_sources_per_query=1)

    pro_arg = pro_agent.generate_argument(topic=topic, round_number=1)
    con_arg = con_agent.generate_argument(topic=topic, round_number=1, opponent_argument=pro_arg)

    # Resolve Empirical Clashes
    resolution = conflict_resolver.resolve_clash(
        topic=topic,
        pro_arg=pro_arg,
        con_arg=con_arg,
        session_id=session_id
    )

    print("\n" + "=" * 60)
    print("CONFLICT RESOLUTION REPORT")
    print("=" * 60)
    print(f"Direct Conflict Detected: {resolution.has_direct_conflict}")
    print(f"Favored Side:             {resolution.favored_side}")
    print(f"Empirical Ground Truth:   {resolution.empirical_ground_truth}")
    print(f"Resolution Notes:         {resolution.resolution_notes}")

if __name__ == "__main__":
    test_conflict_resolver()
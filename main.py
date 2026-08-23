from agents.research_agent import research_agent
from db.chroma_client import evidence_store
from db.supabase_client import supabase_store

def test_research_agent():
    topic = "Should universal basic income be implemented globally?"
    result = research_agent.conduct_research(topic=topic, max_sources_per_query=1)
    
    print("\n" + "="*50)
    print("RESEARCH PIPELINE SUMMARY")
    print("="*50)
    print(f"Total Sources Discovered: {len(result.sources_discovered)}")
    print(f"Total Evidence Extracted: {len(result.extracted_evidence)}")

def test_supabase():
    print("Testing Supabase connection...")
    session_id = supabase_store.create_session(topic="Test Debate Motion")
    if session_id:
        print(f"Connection successful! Created test session: {session_id}")
    else:
        print("Failed to connect to Supabase. Check your .env credentials.")

if __name__ == "__main__":
    # test_research_agent()
    test_supabase()
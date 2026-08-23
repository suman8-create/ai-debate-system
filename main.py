import uuid
from agents.research_agent import research_agent
from agents.audit_agent import audit_agent
from db.chroma_client import evidence_store
from db.supabase_client import supabase_store
from schemas.argument_schema import StructuredArgument
from schemas.evidence_schema import EvidenceUnit

def test_supabase():
    print("Testing Supabase connection...")
    session_id = supabase_store.create_session(topic="Test Debate Motion")
    if session_id:
        print(f"Connection successful! Created test session: {session_id}")
    else:
        print("Failed to connect to Supabase. Check your .env credentials.")

def test_research_agent():
    topic = "Should universal basic income be implemented globally?"
    result = research_agent.conduct_research(topic=topic, max_sources_per_query=1)
    
    print("\n" + "="*50)
    print("RESEARCH PIPELINE SUMMARY")
    print("="*50)
    print(f"Total Sources Discovered: {len(result.sources_discovered)}")
    print(f"Total Evidence Extracted: {len(result.extracted_evidence)}")
    
    print("\n--- Verifying ChromaDB Retrieval ---")
    pro_query = "economic inflation and poverty reduction effects of cash transfers"
    matches = evidence_store.search_evidence(query=pro_query, k=2)
    for i, doc in enumerate(matches, 1):
        print(f"\n[Retrieved Evidence {i}]")
        print(f"Text: {doc.page_content[:150]}...")
        print(f"Source: {doc.metadata.get('source_url')}")

def test_audit_agent():
    topic = "Should universal basic income be implemented globally?"
    session_id = supabase_store.create_session(topic=topic)
    print(f"Created Test Session: {session_id}")

    # Case 1: Grounded, well-evidenced argument
    valid_arg = StructuredArgument(
        argument_id=f"ARG-{uuid.uuid4().hex[:6].upper()}",
        round_number=1,
        side="PRO",
        argument_type="CONSTRUCTIVE",
        claim="Universal Basic Income reduces extreme poverty and improves household financial stability.",
        evidence=EvidenceUnit(
            evidence_id="ev_001",
            claim_text="UBI transfers increased savings and nutrition in pilot programs.",
            quote="Direct cash transfers in regional pilots resulted in a 40% reduction in severe poverty and increased food security.",
            source_url="https://worldbank.org/research/ubi-pilots",
            publisher="World Bank",
            evidence_score=0.9
        ),
        reasoning="When individuals receive unconditional cash, they can cover essential necessities without the administrative overhead of conditional welfare programs.",
        impact="This creates an economic floor that protects vulnerable populations from shocks and cyclical poverty.",
        source_citation="https://worldbank.org/research/ubi-pilots"
    )

    print("\n--- Test 1: Grounded Argument ---")
    res1 = audit_agent.audit_argument(argument=valid_arg, topic=topic, session_id=session_id)
    print(f"Verdict:           {res1.verdict}")
    print(f"Evidence Validity: {res1.evidence_validity}")
    print(f"Logical Strength:  {res1.logical_strength_score}")
    print(f"Fallacies:         {[f.value if hasattr(f, 'value') else f for f in res1.detected_fallacies]}")
    print(f"Feedback:          {res1.feedback_notes}")

    # Case 2: Hallucinated / Unsupported claim
    unsupported_arg = StructuredArgument(
        argument_id=f"ARG-{uuid.uuid4().hex[:6].upper()}",
        round_number=1,
        side="CON",
        argument_type="CONSTRUCTIVE",
        claim="UBI immediately collapses national GDP by 90% within three weeks of implementation.",
        evidence=EvidenceUnit(
            evidence_id="ev_002",
            claim_text="Modest cash transfers slightly shifted part-time work hours.",
            quote="Researchers observed a minor 2% reduction in total work hours among secondary earners.",
            source_url="https://example.com/blog",
            publisher="Example Blog",
            evidence_score=0.4
        ),
        reasoning="Because everyone gets free money, nobody will ever work again and civilization will end.",
        impact="Complete collapse of all global production.",
        source_citation="https://example.com/blog"
    )

    print("\n--- Test 2: Hallucinated / Extreme Argument ---")
    res2 = audit_agent.audit_argument(argument=unsupported_arg, topic=topic, session_id=session_id)
    print(f"Verdict:           {res2.verdict}")
    print(f"Evidence Validity: {res2.evidence_validity}")
    print(f"Logical Strength:  {res2.logical_strength_score}")
    print(f"Fallacies:         {[f.value if hasattr(f, 'value') else f for f in res2.detected_fallacies]}")
    print(f"Feedback:          {res2.feedback_notes}")

if __name__ == "__main__":
    # Run whichever test you want:
    # test_supabase()
    # test_research_agent()
    test_audit_agent()
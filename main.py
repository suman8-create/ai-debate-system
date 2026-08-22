from agents.research_agent import research_agent
from db.chroma_client import evidence_store

def test_research_agent():
    topic = "Should universal basic income be implemented globally?"
    
    # 1. Run the research agent
    result = research_agent.conduct_research(topic=topic, max_sources_per_query=1)
    
    print("\n" + "="*50)
    print("RESEARCH PIPELINE SUMMARY")
    print("="*50)
    print(f"Total Sources Discovered: {len(result.sources_discovered)}")
    print(f"Total Evidence Extracted: {len(result.extracted_evidence)}")
    
    # 2. Test semantic search against the newly indexed evidence
    print("\n--- Verifying ChromaDB Retrieval from Live Research ---")
    pro_query = "economic inflation and poverty reduction effects of cash transfers"
    matches = evidence_store.search_evidence(query=pro_query, k=2)
    
    for i, doc in enumerate(matches, 1):
        print(f"\n[Retrieved Evidence {i}]")
        print(f"Text:\n{doc.page_content}")
        print(f"Source: {doc.metadata.get('source_url')}")
        print(f"Score: {doc.metadata.get('evidence_score')}")

if __name__ == "__main__":
    test_research_agent()
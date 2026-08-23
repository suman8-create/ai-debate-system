import uuid
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from agents.audit_agent import audit_agent
from agents.research_agent import research_agent
from config.settings import settings
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

  print("\n" + "=" * 50)
  print("RESEARCH PIPELINE SUMMARY")
  print("=" * 50)
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
  topic = "Makeup is harmfull"

  # 1. Create a live Supabase session
  print("=" * 60)
  print("STEP 1: CREATING DEBATE SESSION IN SUPABASE")
  print("=" * 60)
  session_id = supabase_store.create_session(topic=topic)
  print(f"Active Session UUID: {session_id}")

  # 2. Conduct real-time web research & indexing
  print("\n" + "=" * 60)
  print("STEP 2: CONDUCTING REAL-TIME RESEARCH & VECTOR INDEXING")
  print("=" * 60)
  research_result = research_agent.conduct_research(
      topic=topic, max_sources_per_query=1
  )
  print(f"Total Sources Discovered: {len(research_result.sources_discovered)}")
  print(f"Total Evidence Extracted: {len(research_result.extracted_evidence)}")

  # 3. Retrieve top relevant evidence from ChromaDB
  print("\n" + "=" * 60)
  print("STEP 3: SEMANTIC SEARCH FROM CHROMADB")
  print("=" * 60)
  search_query = (
      "{topic} health risks dermatology chemical toxicity"
  )
  retrieved_docs = evidence_store.search_evidence(query=search_query, k=1)

  if not retrieved_docs:
    print("No evidence found in ChromaDB. Exiting audit test.")
    return

  doc = retrieved_docs[0]
  meta = doc.metadata
  print(f"Retrieved Source:  {meta.get('source_url')}")
  print(f"Retrieved Snippet: {doc.page_content[:180]}...")

  live_evidence = EvidenceUnit(
      evidence_id=f"ev_{uuid.uuid4().hex[:6]}",
      claim_text=doc.page_content[:200],
      quote=doc.page_content,
      source_url=meta.get("source_url", "https://example.com"),
      publisher=meta.get("publisher", "Web Source"),
      evidence_score=float(meta.get("evidence_score", 0.8)),
  )

  # 4. Dynamic LLM Argument Generation (Zero Hardcoding)
  print("\n" + "=" * 60)
  print("STEP 4: DYNAMIC LLM ARGUMENT GENERATION FROM EVIDENCE")
  print("=" * 60)
  llm = ChatOllama(
      model=settings.REASONING_MODEL,
      base_url=settings.OLLAMA_BASE_URL,
      temperature=0.7,
  )
  structured_llm = llm.with_structured_output(StructuredArgument)

  prompt = ChatPromptTemplate.from_messages([
      (
          "system",
          "You are an expert affirmative (PRO) debater in a competitive"
          " dialectical debate.\nConstruct a structured argument adhering to"
          " the strict 5-tier schema.\nYou MUST ground your claim, reasoning,"
          " and impact directly in the provided evidence quote.",
      ),
      (
          "human",
          "Debate Topic: {topic}\nAssigned Side: PRO\nRound Number:"
          " 1\nEvidence Quote: {quote}\nEvidence Source: {source_url}\n\nGenerate"
          " a StructuredArgument containing claim, reasoning, and impact.",
      ),
  ])

  chain = prompt | structured_llm
  generated_arg = chain.invoke({
      "topic": topic,
      "quote": live_evidence.quote,
      "source_url": live_evidence.source_url,
  })

  generated_arg.evidence = live_evidence
  generated_arg.source_citation = live_evidence.source_url
  generated_arg.side = "PRO"
  generated_arg.argument_type = "CONSTRUCTIVE"
  generated_arg.round_number = 1

  print(f"\n[Generated Argument ID]: {generated_arg.argument_id}")
  print(f"Side:      {generated_arg.side}")
  print(f"Claim:     {generated_arg.claim}")
  print(f"Reasoning: {generated_arg.reasoning}")
  print(f"Impact:    {generated_arg.impact}")
  print(f"Source:    {generated_arg.source_citation}")

  # 5. Run the Audit Agent
  print("\n" + "=" * 60)
  print("STEP 5: AUDIT AGENT VERIFICATION & SUPABASE PERSISTENCE")
  print("=" * 60)
  audit_verdict = audit_agent.audit_argument(
      argument=generated_arg, topic=topic, session_id=session_id
  )

  print(f"\n--- AUDIT SCORECARD ---")
  print(f"Verdict:              {audit_verdict.verdict}")
  print(f"Evidence Grounding:   {audit_verdict.evidence_validity}")
  print(f"Logical Strength:     {audit_verdict.logical_strength_score}")
  print(f"Source Quality:       {audit_verdict.source_quality_score}")
  print(f"Topic Relevance:      {audit_verdict.relevance_score}")
  print(
      "Fallacies Detected:  "
      f" {[f.value if hasattr(f, 'value') else f for f in audit_verdict.detected_fallacies]}"
  )
  print(f"Feedback / Notes:     {audit_verdict.feedback_notes}")

  # 6. Verify Supabase record
  print("\n" + "=" * 60)
  print("STEP 6: VERIFYING SUPABASE PERSISTENCE")
  print("=" * 60)
  saved_arguments = supabase_store.get_session_arguments(session_id)
  print(
      "Total arguments saved for this session in Supabase:"
      f" {len(saved_arguments)}"
  )
  if saved_arguments:
    latest = saved_arguments[-1]
    print(f"Persisted Claim: {latest.get('claim')}")


if __name__ == "__main__":
  # test_supabase()
  # test_research_agent()
  test_audit_agent()
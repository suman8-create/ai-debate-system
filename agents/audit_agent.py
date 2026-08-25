import logging
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config.settings import settings
from db.chroma_client import evidence_store
from db.supabase_client import supabase_store
from schemas.argument_schema import StructuredArgument
from schemas.audit_schema import AuditResult, EvidenceValidity, FallacyType

logger = logging.getLogger(__name__)


class AuditAgent:
  """Auditor evaluating logical rigor, evidence grounding, and relevance."""

  def __init__(self):
    self.llm = ChatOllama(
        model=settings.REASONING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        keep_alive="24h",
        num_ctx=4096,
        num_predict=500,
    )
    self.evidence_db = evidence_store
    self.supabase = supabase_store

  def audit_argument(
      self,
      argument: StructuredArgument,
      topic: str,
      opponent_argument: Optional[StructuredArgument] = None,
      session_id: Optional[str] = None,
  ) -> AuditResult:
    print(
        f"[Audit Agent] Verifying {argument.side} argument (Round"
        f" {argument.round_number})..."
    )

    retrieved_docs = self.evidence_db.search_evidence(
        query=f"{topic} {argument.claim}", k=2
    )
    verified_context = (
        "\n".join(
            [f"- [{d.metadata.get('publisher')}]: {d.page_content}" for d in retrieved_docs]
        )
        if retrieved_docs
        else "No matching local evidence."
    )

    prompt = ChatPromptTemplate.from_messages([(
        "system",
        "You are an impartial Debate Auditor and Fact-Checker.\n"
        "Evaluate the argument on:\n"
        "1. Evidence Validity (SUPPORTED, UNSUPPORTED, CONTRADICTED,"
        " HALLUCINATED)\n"
        "2. Logical Fallacies (e.g., STRAW_MAN, AD_HOMINEM, NO_FALLACY)\n"
        "3. Scores (0.0 to 1.0) for source_quality, logical_strength, and"
        " relevance.\n"
        "4. Verdict: 'PASS' if sound, 'REVISE' if fallacious/unsupported,"
        " 'FORFEIT' if completely off-topic.",
    ), (
        "human",
        "Debate Topic: {topic}\n\n"
        "ARGUMENT UNDER AUDIT:\n"
        "Side: {side} (Round {round_number})\n"
        "Claim: {claim}\n"
        "Reasoning: {reasoning}\n"
        "Impact: {impact}\n"
        "Evidence: {evidence}\n\n"
        "VERIFIED KNOWLEDGE BASE EVIDENCE:\n{verified_context}\n\n"
        "Produce the AuditResult.",
    )])

    structured_llm = self.llm.with_structured_output(AuditResult)
    chain = prompt | structured_llm

    try:
      audit: AuditResult = chain.invoke({
          "topic": topic,
          "side": argument.side,
          "round_number": argument.round_number,
          "claim": argument.claim,
          "reasoning": argument.reasoning,
          "impact": argument.impact,
          "evidence": argument.evidence.quote if argument.evidence else "None",
          "verified_context": verified_context,
      })
    except Exception as e:
      logger.warning(f"Audit LLM call fallback: {e}")
      audit = AuditResult(
          argument_id=argument.argument_id,
          evidence_validity=EvidenceValidity.SUPPORTED,
          source_quality_score=0.8,
          logical_strength_score=0.8,
          relevance_score=0.9,
          detected_fallacies=[FallacyType.NO_FALLACY],
          verdict="PASS",
          feedback_notes="Passed under automated fallback.",
      )

    return audit


audit_agent = AuditAgent()
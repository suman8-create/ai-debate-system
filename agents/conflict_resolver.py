import logging
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.conflict_schema import ConflictResolution
from db.chroma_client import evidence_store
from db.supabase_client import supabase_store

logger = logging.getLogger(__name__)

class ConflictResolverAgent:
    """Specialized referee that resolves direct factual and statistical contradictions between debaters."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
            keep_alive="24h",
            num_ctx=2048
        )
        self.evidence_db = evidence_store
        self.supabase = supabase_store

    def resolve_clash(
        self,
        topic: str,
        pro_arg: StructuredArgument,
        con_arg: StructuredArgument,
        session_id: Optional[str] = None
    ) -> ConflictResolution:
        print(f"\n[Conflict Resolver] Analyzing factual alignment for Round {pro_arg.round_number}...")

        # Semantic search for ground truth verification
        clash_query = f"{topic} factual evidence {pro_arg.claim} versus {con_arg.claim}"
        retrieved_docs = self.evidence_db.search_evidence(query=clash_query, k=3)

        evidence_context = "\n".join([
            f"- [{doc.metadata.get('publisher', 'Source')}]: {doc.page_content}"
            for doc in retrieved_docs
        ]) if retrieved_docs else "No specific ground truth document found in local store."

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an impartial Empirical Fact-Checker and Conflict Resolver in a competitive debate.\n"
                "Your job is to analyze two opposing arguments, detect whether they present contradictory facts or statistics, "
                "and reconcile the conflict against the provided Ground Truth Evidence.\n\n"
                "RULES:\n"
                "1. Identify if there is an explicit empirical clash (not just differing values or interpretations).\n"
                "2. Determine which stance is better supported by empirical evidence.\n"
                "3. Provide the definitive empirical ground truth."
            ),
            (
                "human",
                "Debate Topic: {topic}\n\n"
                "PRO ARGUMENT:\n"
                "Claim: {pro_claim}\n"
                "Reasoning: {pro_reasoning}\n"
                "Evidence Cited: {pro_evidence}\n\n"
                "CON ARGUMENT:\n"
                "Claim: {con_claim}\n"
                "Reasoning: {con_reasoning}\n"
                "Evidence Cited: {con_evidence}\n\n"
                "VERIFIED GROUND TRUTH EVIDENCE:\n{evidence_context}\n\n"
                "Generate the complete ConflictResolution."
            )
        ])

        structured_llm = self.llm.with_structured_output(ConflictResolution)
        chain = prompt | structured_llm

        resolution: ConflictResolution = chain.invoke({
            "topic": topic,
            "pro_claim": pro_arg.claim,
            "pro_reasoning": pro_arg.reasoning,
            "pro_evidence": pro_arg.evidence.quote if pro_arg.evidence else "None",
            "con_claim": con_arg.claim,
            "con_reasoning": con_arg.reasoning,
            "con_evidence": con_arg.evidence.quote if con_arg.evidence else "None",
            "evidence_context": evidence_context
        })

        # Persist to Supabase
        if session_id:
            try:
                self.supabase.client.table("conflict_resolutions").insert({
                    "session_id": session_id,
                    "has_direct_conflict": resolution.has_direct_conflict,
                    "favored_side": resolution.favored_side,
                    "conflicting_claims": resolution.conflicting_claims,
                    "empirical_ground_truth": resolution.empirical_ground_truth,
                    "resolution_notes": resolution.resolution_notes
                }).execute()
            except Exception as e:
                logger.warning(f"Could not persist conflict resolution to Supabase: {e}")

        return resolution

conflict_resolver = ConflictResolverAgent()
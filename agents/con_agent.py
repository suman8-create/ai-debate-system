import logging
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.evidence_schema import EvidenceUnit
from db.chroma_client import evidence_store
from db.supabase_client import supabase_store

logger = logging.getLogger(__name__)

class ConDebateAgent:
    """Negative debater agent that constructs structured, grounded counter-arguments opposing the motion."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7
        )
        self.evidence_db = evidence_store
        self.supabase = supabase_store

    def generate_argument(
        self,
        topic: str,
        round_number: int = 1,
        opponent_argument: Optional[StructuredArgument] = None,
        audit_feedback: Optional[str] = None
    ) -> StructuredArgument:
        """Constructs a 5-tier CON counter-argument or rebuttal based on ChromaDB evidence."""
        arg_type = "CONSTRUCTIVE" if round_number == 1 else "REBUTTAL"
        print(f"\n[CON Agent] Generating {arg_type} for Round {round_number}...")

        if opponent_argument:
            search_query = f"{topic} negative counter-argument rebutting {opponent_argument.claim}"
        else:
            search_query = f"{topic} risks disadvantages harms drawbacks evidence opposing"

        retrieved_docs = self.evidence_db.search_evidence(query=search_query, k=2)

        live_evidence: Optional[EvidenceUnit] = None
        evidence_quote = "No explicit quote retrieved. Ground argument using strict deductive logic."
        evidence_source = None

        if retrieved_docs:
            doc = retrieved_docs[0]
            meta = doc.metadata
            evidence_quote = doc.page_content
            evidence_source = meta.get("source_url")
            live_evidence = EvidenceUnit(
                evidence_id=meta.get("evidence_id", f"ev_con_{round_number}"),
                claim_text=doc.page_content[:200],
                quote=doc.page_content,
                source_url=evidence_source or "https://evidence.source",
                publisher=meta.get("publisher", "Research Source"),
                evidence_score=float(meta.get("evidence_score", 0.8))
            )

        revision_context = (
            f"PREVIOUS ATTEMPT FAILED AUDIT. Auditor Feedback: {audit_feedback}\nFix these issues completely!"
            if audit_feedback else "Initial attempt for this round."
        )

        opponent_context = (
            f"Opponent Claim: {opponent_argument.claim}\n"
            f"Opponent Reasoning: {opponent_argument.reasoning}\n"
            f"Target Claim ID: {opponent_argument.argument_id}"
            if opponent_argument else "No opponent argument (Opening Round)."
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an elite, Oxford-style negative (CON) debater in a competitive dialectical debate.\n"
                "Your objective is to construct a rigorous argument refuting the topic or dismantling the PRO side's claims.\n\n"
                "Rules:\n"
                "1. Strictly ground your claim, reasoning, and impact in the provided Evidence Quote.\n"
                "2. If this is a REBUTTAL, directly attack the opponent's premise or provide a superior counter-model.\n"
                "3. Avoid logical fallacies (no straw man, no slippery slope).\n"
                "4. Make the reasoning deductively tight and highlight systemic harms or costs."
            ),
            (
                "human",
                "Debate Topic: {topic}\n"
                "Side: CON\n"
                "Round: {round_number}\n"
                "Argument Type: {arg_type}\n\n"
                "REVISION / AUDIT STATUS:\n{revision_status}\n\n"
                "OPPONENT ARGUMENT (To Rebut):\n{opp_context}\n\n"
                "GROUNDING EVIDENCE:\nQuote: {quote}\nSource: {source}\n\n"
                "Generate the StructuredArgument containing claim, reasoning, and impact."
            )
        ])

        structured_llm = self.llm.with_structured_output(StructuredArgument)
        chain = prompt | structured_llm

        argument = chain.invoke({
            "topic": topic,
            "round_number": round_number,
            "arg_type": arg_type,
            "revision_status": revision_context,
            "opp_context": opponent_context,
            "quote": evidence_quote,
            "source": evidence_source or "Unspecified"
        })


        argument.side = "CON"
        argument.round_number = round_number
        argument.argument_type = arg_type
        argument.evidence = live_evidence
        argument.source_citation = evidence_source
        if opponent_argument:
            argument.target_claim_id = opponent_argument.argument_id

        return argument

con_agent = ConDebateAgent()
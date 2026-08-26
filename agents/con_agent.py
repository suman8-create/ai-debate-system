import logging
from typing import Optional, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.argument_schema import StructuredArgument, ArgumentType
from schemas.evidence_schema import EvidenceUnit
from db.chroma_client import evidence_store

logger = logging.getLogger(__name__)

class ConDebaterAgent:
    """Specialized CON debater generating structured, opposition evidence-backed counter-arguments."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.5,
            keep_alive="24h",
            num_ctx=4096,
            num_predict=700
        )
        self.evidence_db = evidence_store

    def generate_argument(
        self,
        topic: str,
        round_number: int,
        opponent_argument: Optional[StructuredArgument] = None,
        audit_feedback: Optional[str] = None,
        prior_arguments: Optional[List[StructuredArgument]] = None
    ) -> StructuredArgument:
        arg_type = ArgumentType.CONSTRUCTIVE if round_number == 1 else (
            ArgumentType.REBUTTAL if round_number == 2 else ArgumentType.CLOSING
        )

        print(f"\n[CON Agent] Querying Vector DB for OPPOSITION evidence ({arg_type.value})...")

        retrieval_query = f"{topic} taxpayer cost burden degree inflation quality reduction unintended consequences"
        retrieved_docs = self.evidence_db.search_evidence(query=retrieval_query, k=3)

        evidence_options = []
        for idx, doc in enumerate(retrieved_docs, start=1):
            evidence_options.append(
                f"Evidence Item {idx}: \"{doc.page_content}\" [Publisher: {doc.metadata.get('publisher', 'Source')} | URL: {doc.metadata.get('source_url', 'N/A')}]"
            )
        evidence_context = "\n".join(evidence_options) if evidence_options else "No direct evidence retrieved."

        history_context = "None (Opening Turn)"
        if prior_arguments:
            history_context = "\n".join([
                f"- [Round {a.round_number} {a.side}]: {a.claim}" for a in prior_arguments
            ])

        opponent_context = "None (Opening Round)"
        target_claim_id = None
        if opponent_argument:
            opponent_context = (
                f"Opponent Claim (ID: {opponent_argument.argument_id}): {opponent_argument.claim}\n"
                f"Opponent Reasoning: {opponent_argument.reasoning}\n"
                f"Opponent Impact: {opponent_argument.impact}"
            )
            target_claim_id = opponent_argument.argument_id

        feedback_instruction = (
            f"\nAUDITOR REVISION GUIDANCE (FIX THESE ISSUES):\n'{audit_feedback}'\nYou MUST adjust your argument to address this."
            if audit_feedback else ""
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an elite Oxford-Style Debater representing the CON (Opposition) side.\n\n"
                "STRICT RULES:\n"
                "1. You must ALWAYS argue AGAINST the motion.\n"
                "2. Your claim and reasoning MUST expose negative trade-offs (e.g., taxpayer burden, credential inflation, classroom overcrowding, misallocation of public funds).\n"
                "3. In Round 2 (REBUTTAL), directly challenge the PRO assertion with counter-data.\n"
                "4. DO NOT cite affirmative quotes as your justification."
            ),
            (
                "human",
                "Debate Topic: {topic}\n"
                "Role: CON (Opposition)\n"
                "Stage: Round {round_number} ({arg_type})\n\n"
                "RETRIEVED OPPOSITION EVIDENCE:\n{evidence_context}\n\n"
                "PREVIOUS DEBATE TURNS:\n{history_context}\n\n"
                "PRO OPPONENT ARGUMENT TO REFUTE:\n{opponent_context}\n"
                "{feedback_instruction}\n\n"
                "Draft your opposition StructuredArgument."
            )
        ])

        structured_llm = self.llm.with_structured_output(StructuredArgument)
        chain = prompt | structured_llm

        arg: StructuredArgument = chain.invoke({
            "topic": topic,
            "round_number": round_number,
            "arg_type": arg_type.value,
            "evidence_context": evidence_context,
            "history_context": history_context,
            "opponent_context": opponent_context,
            "feedback_instruction": feedback_instruction
        })

        arg.side = "CON"
        arg.round_number = round_number
        arg.argument_type = arg_type
        if target_claim_id:
            arg.target_claim_id = target_claim_id

        return arg

con_agent = ConDebaterAgent()
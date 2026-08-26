import logging
from typing import Optional, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.argument_schema import StructuredArgument, ArgumentType
from schemas.evidence_schema import EvidenceUnit
from db.chroma_client import evidence_store

logger = logging.getLogger(__name__)

class ProDebaterAgent:
    """Specialized PRO debater generating structured, affirmative evidence-backed arguments."""

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

        print(f"\n[PRO Agent] Querying Vector DB for AFFIRMATIVE evidence ({arg_type.value})...")

        retrieval_query = f"{topic} positive economic benefits higher wages social mobility ROI statistics"
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
                "You are an elite Oxford-Style Debater representing the PRO (Affirmative) side.\n\n"
                "STRICT RULES:\n"
                "1. You must ALWAYS argue in FAVOR of the topic.\n"
                "2. Your claim and reasoning MUST align with affirmative points (e.g., higher graduation rates, reduced debt, positive GDP return).\n"
                "3. In Round 2 (REBUTTAL), deconstruct the opponent's counter-argument and prove why affirmative benefits outweigh their concerns.\n"
                "4. DO NOT cite negative or contrary quotes as your own justification."
            ),
            (
                "human",
                "Debate Topic: {topic}\n"
                "Role: PRO (Affirmative)\n"
                "Stage: Round {round_number} ({arg_type})\n\n"
                "RETRIEVED AFFIRMATIVE EVIDENCE:\n{evidence_context}\n\n"
                "PREVIOUS DEBATE TURNS:\n{history_context}\n\n"
                "CON OPPONENT ARGUMENT TO REFUTE:\n{opponent_context}\n"
                "{feedback_instruction}\n\n"
                "Draft your affirmative StructuredArgument."
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

        arg.side = "PRO"
        arg.round_number = round_number
        arg.argument_type = arg_type
        if target_claim_id:
            arg.target_claim_id = target_claim_id

        return arg

pro_agent = ProDebaterAgent()
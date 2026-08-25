import logging
from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.judge_schema import AdjudicationVerdict
from db.supabase_client import supabase_store

logger = logging.getLogger(__name__)

class JudgeAgent:
    """Chief Adjudicator that objectively analyzes full debate transcripts and renders verdicts."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,
            keep_alive="1h",
            num_ctx=4096
        )
        self.supabase = supabase_store

    def adjudicate_debate(
        self,
        topic: str,
        arguments: List[StructuredArgument],
        session_id: Optional[str] = None
    ) -> AdjudicationVerdict:
        print(f"\n[Judge Agent] Evaluating complete transcript of {len(arguments)} arguments...")

        # 1. Format Debate Transcript
        transcript_blocks = []
        for arg in arguments:
            evidence_info = (
                f"Evidence: \"{arg.evidence.quote}\" (Source: {arg.evidence.source_url})"
                if arg.evidence else "Evidence: None provided"
            )
            target_info = f" [Rebutting: {arg.target_claim_id}]" if arg.target_claim_id else ""

            block = (
                f"=== ROUND {arg.round_number} | SIDE: {arg.side} | TYPE: {arg.argument_type}{target_info} ===\n"
                f"Argument ID: {arg.argument_id}\n"
                f"Claim: {arg.claim}\n"
                f"Reasoning: {arg.reasoning}\n"
                f"Impact: {arg.impact}\n"
                f"{evidence_info}\n"
            )
            transcript_blocks.append(block)

        full_transcript = "\n".join(transcript_blocks)

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are the Chief Adjudicator of an elite Oxford-Style competitive debate.\n"
                "Your duty is to judge the debate impartially and strictly based on the record.\n\n"
                "SCORING GUIDELINES (100 Points Total per side):\n"
                "1. Argumentation Strength (0-30): Logical consistency, premise validity, and deductive depth.\n"
                "2. Evidence Quality (0-25): Factual grounding, citation relevance, and avoidance of unsupported claims.\n"
                "3. Rebuttal Effectiveness (0-25): Direct refutation of opponent points, exposing flaws, and counter-models.\n"
                "4. Persuasion & Impact (0-20): Comparative weighing of outcomes and systemic societal consequences.\n\n"
                "RULES:\n"
                "- Do not let personal bias dictate the winner.\n"
                "- The side that won key clashes and successfully defended against rebuttals must win."
            ),
            (
                "human",
                "DEBATE TOPIC: {topic}\n\n"
                "COMPLETE DEBATE TRANSCRIPT:\n{transcript}\n\n"
                "Evaluate the debate and generate the complete AdjudicationVerdict."
            )
        ])

        structured_llm = self.llm.with_structured_output(AdjudicationVerdict)
        chain = prompt | structured_llm

        verdict: AdjudicationVerdict = chain.invoke({
            "topic": topic,
            "transcript": full_transcript
        })

        # Persist Verdict to Supabase if session_id exists
        iif session_id:
            try:
                update_payload = {
                    "status": "COMPLETED",
                    "winner": verdict.winner.value,
                    "metadata": verdict.model_dump()
                }
                self.supabase.client.table("debate_sessions").update(update_payload).eq("id", session_id).execute()
                print(f"[Judge Agent] Adjudication persisted to Supabase for session: {session_id}")
            except Exception as e:
                logger.warning(f"Could not update session metadata in Supabase: {e}")

        return verdict

judge_agent = JudgeAgent()
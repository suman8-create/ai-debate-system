import logging
from typing import Any, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config.settings import settings
from db.supabase_client import supabase_store
from schemas.argument_schema import StructuredArgument
from schemas.judge_schema import AdjudicationVerdict

logger = logging.getLogger(__name__)


class JudgeAgent:
    """Chief Adjudicator that objectively analyzes full debate transcripts and renders verdicts."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,
            keep_alive="24h",
            num_ctx=4096,
        )
        self.supabase = supabase_store

    def adjudicate_debate(
        self,
        topic: str,
        arguments: List[StructuredArgument],
        conflict_history: Optional[List[Any]] = None,
        session_id: Optional[str] = None,
    ) -> AdjudicationVerdict:
        print(
            f"\n[Judge Agent] Evaluating transcript with {len(arguments)} arguments and {len(conflict_history or [])} resolved clashes..."
        )

        # Format transcript
        transcript_blocks = []
        for arg in arguments:
            evidence_info = (
                f'Evidence: "{arg.evidence.quote}" (Source: {arg.evidence.source_url})'
                if arg.evidence
                else "Evidence: None provided"
            )
            arg_type_val = (
                arg.argument_type.value
                if hasattr(arg.argument_type, "value")
                else arg.argument_type
            )
            target_info = f" [Rebutting: {arg.target_claim_id}]" if getattr(arg, "target_claim_id", None) else ""

            block = (
                f"=== ROUND {arg.round_number} | SIDE: {arg.side} | TYPE: {arg_type_val}{target_info} ===\n"
                f"Argument ID: {arg.argument_id}\n"
                f"Claim: {arg.claim}\n"
                f"Reasoning: {arg.reasoning}\n"
                f"Impact: {arg.impact}\n"
                f"{evidence_info}\n"
            )
            transcript_blocks.append(block)

        full_transcript = "\n".join(transcript_blocks)

        # Format conflict reports
        conflict_report = "No direct empirical conflicts detected."
        if conflict_history:
            conflict_report = "\n".join(
                [
                    f"- Round Clash: Favored {c.favored_side} | Ground Truth: {c.empirical_ground_truth}"
                    for c in conflict_history
                ]
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Chief Adjudicator of an elite Oxford-Style debate.\n"
                    "Judge the debate impartially based strictly on the record and the Empirical Fact-Checker report.\n\n"
                    "SCORING CRITERIA (100 Points Total per side):\n"
                    "1. Argumentation Strength (0-30): Logical consistency and premise validity.\n"
                    "2. Evidence Quality (0-25): Factual grounding and alignment with verified empirical ground truth.\n"
                    "3. Rebuttal Effectiveness (0-25): Direct refutation and defense of key clashes.\n"
                    "4. Persuasion & Impact (0-20): Comparative impact weighing.\n\n"
                    "PENALTY RULE: If a debater was contradicted by the Empirical Fact-Checker report, penalize their Evidence Quality score accordingly.",
                ),
                (
                    "human",
                    "DEBATE TOPIC: {topic}\n\n"
                    "DEBATE TRANSCRIPT:\n{transcript}\n\n"
                    "EMPIRICAL FACT-CHECKER REPORT:\n{conflict_report}\n\n"
                    "Deliver your AdjudicationVerdict.",
                ),
            ]
        )

        structured_llm = self.llm.with_structured_output(AdjudicationVerdict)
        chain = prompt | structured_llm

        verdict: AdjudicationVerdict = chain.invoke(
            {
                "topic": topic,
                "transcript": full_transcript,
                "conflict_report": conflict_report,
            }
        )

        # Persist Verdict to Supabase if session_id exists
        if session_id:
            try:
                update_payload = {
                    "status": "COMPLETED",
                    "winner": verdict.winner.value,
                    "metadata": verdict.model_dump(),
                }
                self.supabase.client.table("debate_sessions").update(update_payload).eq(
                    "id", session_id
                ).execute()
                print(f"[Judge Agent] Adjudication persisted to Supabase for session: {session_id}")
            except Exception as e:
                logger.warning(f"Could not update session metadata in Supabase: {e}")

        return verdict


judge_agent = JudgeAgent()
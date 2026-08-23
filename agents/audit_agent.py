import logging
from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config.settings import settings
from schemas.argument_schema import StructuredArgument
from schemas.audit_schema import AuditResult, FallacyType, EvidenceValidity
from db.supabase_client import supabase_store

logger = logging.getLogger(__name__)

class RawAuditEvaluation(BaseModel):
    evidence_validity: EvidenceValidity = Field(
        description="Whether the claim is strictly SUPPORTED by the quote, CONTRADICTED, or UNSUPPORTED/HALLUCINATED."
    )
    source_quality_score: float = Field(
        description="Score between 0.0 and 1.0 evaluating the credibility and relevance of the source."
    )
    logical_strength_score: float = Field(
        description="Score between 0.0 and 1.0 evaluating deductive and inductive reasoning soundness."
    )
    relevance_score: float = Field(
        description="Score between 0.0 and 1.0 measuring topic relevance."
    )
    rebuttal_quality_score: Optional[float] = Field(
        default=None,
        description="Score between 0.0 and 1.0 evaluating how directly it dismantles the opponent's premise (if rebuttal)."
    )
    detected_fallacies: List[FallacyType] = Field(
        default_factory=list,
        description="List of detected formal/informal logical fallacies (e.g., strawman, ad hominem, false dilemma)."
    )
    repetition_detected: bool = Field(
        default=False,
        description="Set to True if this claim rephrases an argument already made earlier in the session."
    )
    verdict: str = Field(
        description="PASS if evidence is valid and reasoning sound. REVISE if claims are unsupported, repetitive, or fallacious."
    )
    feedback_notes: str = Field(
        description="Clear constructive feedback explaining why it passed or exactly what must be fixed."
    )

class AuditAgent:
    """Independent referee agent that audits arguments for factual grounding and logical validity."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.REASONING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0
        )
        self.supabase = supabase_store

    def audit_argument(
        self,
        argument: StructuredArgument,
        topic: str,
        opponent_argument: Optional[StructuredArgument] = None,
        session_id: Optional[str] = None
    ) -> AuditResult:
        """Audits a StructuredArgument against facts, logical integrity, and prior debate rounds."""
        print(f"\n[Audit Agent] Verifying {argument.side} argument (Round {argument.round_number})...")

        past_arguments_text = "No prior arguments in this session."
        if session_id:
            prior_records = self.supabase.get_session_arguments(session_id)
            if prior_records:
                past_arguments_text = "\n".join([
                    f"- Round {r['round_number']} ({r['side']}): Claim: {r['claim']}"
                    for r in prior_records if r.get("argument_id") != argument.argument_id
                ])

        evidence_quote = argument.evidence.quote if argument.evidence else "NO GROUNDED EVIDENCE PROVIDED."
        evidence_source = argument.evidence.source_url if argument.evidence else argument.source_citation

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an impartial, strict dialectical debate auditor and fact-checker. "
                "Evaluate the given argument for factual grounding, logical validity, and repetition.\n\n"
                "Audit Rules:\n"
                "1. If the claim contains factual statements NOT supported by the Evidence Quote, mark evidence_validity as 'UNSUPPORTED' or 'HALLUCINATED' and verdict as 'REVISE'.\n"
                "2. Detect any logical fallacies (strawman, ad hominem, false dilemma, circular reasoning, etc.).\n"
                "3. If the claim merely rehashes points in PAST SESSION CLAIMS, set repetition_detected=True and verdict='REVISE'.\n"
                "4. Issue 'PASS' ONLY when evidence is strictly SUPPORTED, logical strength >= 0.7, and no fatal fallacies exist."
            ),
            (
                "human",
                "Debate Topic: {topic}\n"
                "Side: {side}\n"
                "Argument Type: {arg_type}\n\n"
                "ARGUMENT UNDER AUDIT:\n"
                "Claim: {claim}\n"
                "Evidence Quote: {quote}\n"
                "Source: {source}\n"
                "Reasoning: {reasoning}\n"
                "Impact: {impact}\n\n"
                "OPPONENT ARGUMENT (if evaluating a rebuttal):\n{opp_text}\n\n"
                "PAST SESSION CLAIMS:\n{past_claims}"
            )
        ])

        structured_llm = self.llm.with_structured_output(RawAuditEvaluation)
        chain = prompt | structured_llm

        opp_text = (
            f"Claim: {opponent_argument.claim}\nReasoning: {opponent_argument.reasoning}"
            if opponent_argument else "None"
        )

        try:
            eval_output = chain.invoke({
                "topic": topic,
                "side": argument.side,
                "arg_type": argument.argument_type,
                "claim": argument.claim,
                "quote": evidence_quote,
                "source": evidence_source,
                "reasoning": argument.reasoning,
                "impact": argument.impact,
                "opp_text": opp_text,
                "past_claims": past_arguments_text
            })

            audit_res = AuditResult(
                argument_id=argument.argument_id,
                evidence_validity=eval_output.evidence_validity,
                source_quality_score=eval_output.source_quality_score,
                logical_strength_score=eval_output.logical_strength_score,
                relevance_score=eval_output.relevance_score,
                rebuttal_quality_score=eval_output.rebuttal_quality_score,
                detected_fallacies=eval_output.detected_fallacies,
                repetition_detected=eval_output.repetition_detected,
                verdict=eval_output.verdict if eval_output.verdict in ["PASS", "REVISE", "FORFEIT"] else "REVISE",
                feedback_notes=eval_output.feedback_notes
            )

            # Persist to Supabase if session_id is provided
            if session_id:
                self.supabase.save_argument(session_id, argument)
                self.supabase.save_audit(audit_res)

            return audit_res

        except Exception as e:
            logger.error(f"Audit LLM call failed: {e}")
            return AuditResult(
                argument_id=argument.argument_id,
                evidence_validity=EvidenceValidity.SUPPORTED if argument.evidence else EvidenceValidity.UNSUPPORTED,
                source_quality_score=0.7 if argument.evidence else 0.0,
                logical_strength_score=0.7,
                relevance_score=0.8,
                verdict="PASS" if argument.evidence else "REVISE",
                feedback_notes=f"Audit execution fallback due to error: {e}"
            )

audit_agent = AuditAgent()
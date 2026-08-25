import logging
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config.settings import settings
from db.chroma_client import evidence_store
from schemas.argument_schema import ArgumentType, StructuredArgument

logger = logging.getLogger(__name__)


class ConDebaterAgent:

  def __init__(self):
    self.llm = ChatOllama(
        model=settings.REASONING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7,  # Essential for diverse counter-argument generation
        keep_alive="24h",
        num_ctx=4096,
        num_predict=700,
    )
    self.evidence_db = evidence_store

  def generate_argument(
      self,
      topic: str,
      round_number: int,
      opponent_argument: Optional[StructuredArgument] = None,
      audit_feedback: Optional[str] = None,
      prior_arguments: Optional[List[StructuredArgument]] = None,
  ) -> StructuredArgument:
    arg_type = (
        ArgumentType.CONSTRUCTIVE
        if round_number == 1
        else (
            ArgumentType.REBUTTAL
            if round_number == 2
            else ArgumentType.CLOSING
        )
    )

    print(f"\n[CON Agent] Generating {arg_type.value} for Round {round_number}...")

    if opponent_argument:
      retrieval_query = (
          f"{topic} harms costs risks unintended consequences against"
          f" {opponent_argument.claim}"
      )
    else:
      retrieval_query = (
          f"{topic} taxpayer burden economic risks diploma devaluation"
          " disadvantages"
      )

    retrieved_docs = self.evidence_db.search_evidence(query=retrieval_query, k=3)
    evidence_context = (
        "\n".join([
            f"- [{doc.metadata.get('publisher', 'Source')}]:"
            f' "{doc.page_content}" (URL:'
            f" {doc.metadata.get('source_url', 'N/A')})"
            for doc in retrieved_docs
        ])
        if retrieved_docs
        else "No direct evidence retrieved."
    )

    history_context = "None (Opening Turn)"
    if prior_arguments:
      history_context = "\n".join([
          f"- [Round {a.round_number} {a.side}]: {a.claim}"
          for a in prior_arguments
      ])

    opponent_context = "None (Opening Round)"
    target_claim_id = None
    if opponent_argument:
      opponent_context = (
          f"Opponent Claim (ID: {opponent_argument.argument_id}):"
          f" {opponent_argument.claim}\nOpponent Reasoning:"
          f" {opponent_argument.reasoning}\nOpponent Impact:"
          f" {opponent_argument.impact}"
      )
      target_claim_id = opponent_argument.argument_id

    feedback_instruction = (
        "\nCRITICAL REVISION DIRECTIVE: Your previous attempt was REJECTED with"
        f" the following auditor feedback:\n'{audit_feedback}'\nYou MUST"
        " completely change your phrasing, use new evidence, and fix these"
        " flaws."
        if audit_feedback
        else ""
    )

    prompt = ChatPromptTemplate.from_messages([(
        "system",
        "You are an elite Oxford-Style Debater representing the CON"
        " (Opposition) side.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. You must ALWAYS argue AGAINST the motion. Never support or affirm"
        " the topic.\n"
        "2. Formulate original arguments (e.g., massive taxpayer burden, degree"
        " inflation, university quality degradation, misallocation of public"
        " funds).\n"
        "3. DO NOT repeat claims from earlier rounds.\n"
        "4. In REBUTTAL rounds, deconstruct the PRO affirmative claim directly"
        " and prove why the proposal causes net societal harm.",
    ), (
        "human",
        "Debate Topic: {topic}\n"
        "Stage: Round {round_number} ({arg_type})\n\n"
        "PREVIOUS ROUNDS:\n{history_context}\n\n"
        "PRO OPPONENT ARGUMENT TO DISMANTLE:\n{opponent_context}\n\n"
        "AVAILABLE RESEARCH EVIDENCE:\n{evidence_context}\n"
        "{feedback_instruction}\n\n"
        "Generate a novel StructuredArgument for the CON side.",
    )])

    structured_llm = self.llm.with_structured_output(StructuredArgument)
    chain = prompt | structured_llm

    arg: StructuredArgument = chain.invoke({
        "topic": topic,
        "round_number": round_number,
        "arg_type": arg_type.value,
        "history_context": history_context,
        "opponent_context": opponent_context,
        "evidence_context": evidence_context,
        "feedback_instruction": feedback_instruction,
    })

    arg.side = "CON"
    arg.round_number = round_number
    arg.argument_type = arg_type
    if target_claim_id:
      arg.target_claim_id = target_claim_id

    return arg


con_agent = ConDebaterAgent()
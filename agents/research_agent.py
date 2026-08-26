import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from config.settings import settings
from db.chroma_client import evidence_store
from schemas.evidence_schema import (
    EvidenceUnit,
    ResearchQueryResult,
    SourceMetadata,
)
from services.search_service import search_service

logger = logging.getLogger(__name__)


class QueryDecompositionOutput(BaseModel):
  queries: List[str] = Field(
      description=(
          "List of 4 concise keyword search phrases covering statistics,"
          " economic benefits, costs/harms, and international case studies."
      )
  )


class RawEvidenceItem(BaseModel):
  claim_text: str = Field(
      description=(
          "The core factual claim with specific statistics, numbers, or"
          " findings."
      )
  )
  quote: str = Field(
      description="Direct excerpt or citation from the text supporting this."
  )


class EvidenceExtractionOutput(BaseModel):
  evidence_items: List[RawEvidenceItem] = Field(
      description=(
          "Extracted atomic evidence points with empirical data or specific"
          " facts."
      )
  )


class ResearchAgent:

  def __init__(self):
    self.llm = ChatOllama(
        model=settings.REASONING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        keep_alive="24h",
        num_ctx=4096,
    )
    self.search_service = search_service
    self.evidence_store = evidence_store

  def decompose_topic(self, topic: str) -> List[str]:
    prompt = ChatPromptTemplate.from_messages([(
        "system",
        "You are an academic research strategist.\n"
        "Break down the debate motion into 4 targeted keyword search queries"
        " (3-6 words each).\n"
        "Target: (1) statistics/costs, (2) economic ROI/benefits, (3) unintended"
        " consequences/harms, (4) international case studies.",
    ), ("human", "Motion: {topic}")])

    structured_llm = self.llm.with_structured_output(QueryDecompositionOutput)
    chain = prompt | structured_llm

    try:
      result = chain.invoke({"topic": topic})
      return result.queries
    except Exception as e:
      logger.error(f"Error decomposing topic: {e}")
      return [
          f"{topic} empirical statistics data",
          f"{topic} economic benefits study",
          f"{topic} risks harms evidence",
          f"{topic} international comparative outcomes",
      ]

  def extract_evidence_from_text(
      self, text: str, source_meta: SourceMetadata
  ) -> List[EvidenceUnit]:
    truncated_text = text[:3500]

    prompt = ChatPromptTemplate.from_messages([(
        "system",
        "You are an evidence extraction engine for competitive debates.\n"
        "Extract 1 to 2 high-impact, verifiable empirical facts from the"
        " text.\n"
        "PRIORITIZE: Concrete statistics (%, $ amounts, ratios), study"
        " findings, and expert institutional conclusions.\n"
        "DO NOT summarize broadly. Extract the exact supporting quote.",
    ), ("human", "Source Text:\n{text}")])

    structured_llm = self.llm.with_structured_output(EvidenceExtractionOutput)
    chain = prompt | structured_llm

    evidence_units: List[EvidenceUnit] = []
    try:
      result = chain.invoke({"text": truncated_text})
      for item in result.evidence_items:
        if len(item.quote.strip()) > 10:
          unit = EvidenceUnit(
              claim_text=item.claim_text,
              quote=item.quote,
              source_url=source_meta.url,
              publisher=source_meta.publisher,
              evidence_score=source_meta.credibility_score,
              status="SUPPORTED",
          )
          evidence_units.append(unit)
    except Exception as e:
      logger.warning(f"Failed to extract structured evidence: {e}")

    return evidence_units

  def conduct_research(
      self, topic: str, max_sources_per_query: int = 1
  ) -> ResearchQueryResult:
    print(f"\n[Research Agent] Starting parallel research for topic: '{topic}'")
    queries = self.decompose_topic(topic)
    print(f"[Research Agent] Generated Sub-queries ({len(queries)}):")
    for q in queries:
      print(f"  -> {q}")

    all_sources: List[SourceMetadata] = []
    scrape_tasks = []

    for q in queries:
      search_hits = self.search_service.search_topic(
          q, max_results=max_sources_per_query
      )
      for hit in search_hits:
        url = hit["url"]
        if any(s.url == url for s in all_sources):
          continue
        source_meta = self.search_service.evaluate_source_metadata(
            url, hit["title"]
        )
        all_sources.append(source_meta)
        scrape_tasks.append((hit, source_meta))

    all_evidence: List[EvidenceUnit] = []

    def _fetch_and_extract(task):
      hit, meta = task
      print(
          f"[Research Agent] Scraping source: {meta.domain} (Credibility:"
          f" {meta.credibility_score})"
      )
      raw_text = self.search_service.scrape_url_content(meta.url)
      text_to_process = (
          raw_text
          if (raw_text and len(raw_text.strip()) > 100)
          else hit.get("snippet", "")
      )
      if text_to_process:
        return self.extract_evidence_from_text(text_to_process, meta)
      return []

    with ThreadPoolExecutor(max_workers=4) as executor:
      results = executor.map(_fetch_and_extract, scrape_tasks)
      for res in results:
        all_evidence.extend(res)

    if all_evidence:
      print(
          f"[Research Agent] Storing {len(all_evidence)} atomic evidence"
          " records in ChromaDB in parallel..."
      )
      self.evidence_store.add_evidence_units(all_evidence)
      print("[Research Agent] Evidence ingestion and vector indexing complete!")
    else:
      print("[Research Agent] Warning: No evidence could be extracted.")

    return ResearchQueryResult(
        topic=topic,
        generated_queries=queries,
        sources_discovered=all_sources,
        extracted_evidence=all_evidence,
    )


research_agent = ResearchAgent()
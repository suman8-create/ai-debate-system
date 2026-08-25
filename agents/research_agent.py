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
          "List of 3-4 concise keyword search phrases covering statistics,"
          " benefits, harms, and case studies."
      )
  )


class RawEvidenceItem(BaseModel):
  claim_text: str = Field(description="The underlying factual assertion.")
  quote: str = Field(
      description="Verbatim or precise extract supporting the claim."
  )


class EvidenceExtractionOutput(BaseModel):
  evidence_items: List[RawEvidenceItem] = Field(
      description="Extracted atomic evidence points from the text."
  )


class ResearchAgent:
  """Agent responsible for topic decomposition, live web search, dynamic source validation, and ChromaDB evidence indexing."""

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
        "You are an expert research assistant preparing background evidence"
        " for an Oxford-style debate.\n"
        "Your task is to break down the debate topic into 4 targeted search"
        " engine queries.\n\n"
        "CRITICAL SEARCH RULES:\n"
        "1. DO NOT write long questions or conversational sentences.\n"
        "2. Output strictly concise 3-to-6 word keyword search phrases (like"
        " you would type into Google or DuckDuckGo).\n"
        "3. Focus on empirical data, academic studies, economic metrics, and"
        " official statistics.\n"
        "4. Include specific angles: (a) statistics/costs, (b) benefits/pros,"
        " (c) harms/cons, (d) comparative international case studies.",
    ), ("human", "Generate 4 keyword search queries for: {topic}")])

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
    truncated_text = text[:3000]

    prompt = ChatPromptTemplate.from_messages([(
        "system",
        "You are a rigorous evidence extraction engine. Extract up to 2"
        " distinct, verifiable, factual claims and quotes from the text. "
        "Do not summarize or invent facts. Return exact extracted quotes.",
    ), ("human", "Source Text:\n{text}")])

    structured_llm = self.llm.with_structured_output(EvidenceExtractionOutput)
    chain = prompt | structured_llm

    evidence_units: List[EvidenceUnit] = []
    try:
      result = chain.invoke({"text": truncated_text})
      for item in result.evidence_items:
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

    # 1. Gather URLs
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

    # 2. Parallel scraping and extraction
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

    # 3. Vector indexing
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
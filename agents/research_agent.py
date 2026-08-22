import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings
from schemas.evidence_schema import EvidenceUnit, SourceMetadata, ResearchQueryResult
from services.search_service import search_service
from db.chroma_client import evidence_store

logger = logging.getLogger(__name__)

class QueryDecompositionOutput(BaseModel):
    queries: List[str] = Field(
        description="List of 3-5 distinct, targeted search queries covering empirical data, pro arguments, and con arguments."
    )

class RawEvidenceItem(BaseModel):
    claim_text: str = Field(description="The underlying factual assertion.")
    quote: str = Field(description="Verbatim or precise extract supporting the claim.")

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
            temperature=0.1
        )
        self.search_service = search_service
        self.evidence_store = evidence_store

    def decompose_topic(self, topic: str) -> List[str]:
        """Deconstructs the debate motion into targeted multi-perspective search queries."""
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an impartial academic research strategist. Deconstruct the given debate topic into 3 to 4 specific, objective search queries. "
                "Ensure queries cover empirical statistics, pro arguments, and con/risk perspectives."
            ),
            ("human", "Debate Topic: {topic}")
        ])
        
        structured_llm = self.llm.with_structured_output(QueryDecompositionOutput)
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({"topic": topic})
            return result.queries
        except Exception as e:
            logger.error(f"Error decomposing topic: {e}")
            return [
                f"{topic} empirical evidence studies",
                f"{topic} advantages benefits",
                f"{topic} disadvantages risks"
            ]

    def extract_evidence_from_text(self, text: str, source_meta: SourceMetadata) -> List[EvidenceUnit]:
        """Extracts atomic evidence units from scraped page text."""
        # prevent context overload
        truncated_text = text[:3000]
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a rigorous evidence extraction engine. Extract up to 2 distinct, verifiable, factual claims and quotes from the text. "
                "Do not summarize or invent facts. Return exact extracted quotes."
            ),
            ("human", "Source Text:\n{text}")
        ])
        
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
                    status="SUPPORTED"
                )
                evidence_units.append(unit)
        except Exception as e:
            logger.warning(f"Failed to extract structured evidence: {e}")
            
        return evidence_units

    def conduct_research(self, topic: str, max_sources_per_query: int = 1) -> ResearchQueryResult:
        """Executes full research workflow: decompose -> search -> scrape -> extract -> index in ChromaDB."""
        print(f"\n[Research Agent] Starting research for topic: '{topic}'")
        
        # 1. Generate multi-perspective sub-queries
        queries = self.decompose_topic(topic)
        print(f"[Research Agent] Generated Sub-queries ({len(queries)}):")
        for q in queries:
            print(f"  -> {q}")

        all_sources: List[SourceMetadata] = []
        all_evidence: List[EvidenceUnit] = []

        # 2. Search and scrape each query
        for q in queries:
            search_hits = self.search_service.search_topic(q, max_results=max_sources_per_query)
            for hit in search_hits:
                url = hit["url"]
                title = hit["title"]
                
                # Check for duplicates
                if any(s.url == url for s in all_sources):
                    continue
                
                source_meta = self.search_service.evaluate_source_metadata(url, title)
                all_sources.append(source_meta)
                
                print(f"[Research Agent] Scraping & evaluating source: {source_meta.domain} (Credibility: {source_meta.credibility_score})")
                raw_text = self.search_service.scrape_url_content(url)
                
                if raw_text and len(raw_text.strip()) > 100:
                    evidence_items = self.extract_evidence_from_text(raw_text, source_meta)
                    all_evidence.extend(evidence_items)
                elif hit.get("snippet"):
                    # Fallback to snippet if full scraping is blocked
                    evidence_items = self.extract_evidence_from_text(hit["snippet"], source_meta)
                    all_evidence.extend(evidence_items)

        # 3. Store curated evidence in ChromaDB
        if all_evidence:
            print(f"[Research Agent] Storing {len(all_evidence)} atomic evidence records in ChromaDB...")
            self.evidence_store.add_evidence_units(all_evidence)
            print("[Research Agent] Evidence ingestion and vector indexing complete!")
        else:
            print("[Research Agent] Warning: No evidence could be extracted.")

        return ResearchQueryResult(
            topic=topic,
            generated_queries=queries,
            sources_discovered=all_sources,
            extracted_evidence=all_evidence
        )

research_agent = ResearchAgent()
import logging
import asyncio
import uuid
import httpx
import trafilatura
from typing import List, Dict, Any
from schemas.evidence_schema import EvidenceUnit
from services.search_service import search_service
from db.chroma_client import chroma_client  
from llm.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class ResearchAgent:
    """Researches, fast-scrapes, extracts high-yield atomic facts, and indexes into ChromaDB."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _get_target_query_count(self, max_rounds: int) -> int:
        if max_rounds <= 2:
            return 2
        elif max_rounds <= 4:
            return 4
        else:
            return 6

    async def _fetch_url_content(self, url: str, client: httpx.AsyncClient) -> Dict[str, str]:
        try:
            resp = await client.get(url, timeout=3.5, follow_redirects=True)
            if resp.status_code == 200 and resp.text:
                extracted = trafilatura.extract(
                    resp.text,
                    include_links=False,
                    include_images=False,
                    include_tables=True,
                    no_fallback=True
                )
                if extracted and len(extracted.strip()) > 200:
                    return {"url": url, "text": extracted[:3000]}
        except Exception:
            pass
        return {"url": url, "text": ""}

    async def _parallel_scrape(self, urls: List[str]) -> List[Dict[str, str]]:
        async with httpx.AsyncClient(headers=self.headers, verify=False) as client:
            tasks = [self._fetch_url_content(url, client) for url in urls[:6]]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r["text"]]

    def generate_sub_queries(self, topic: str, max_rounds: int = 2) -> List[str]:
        query_count = self._get_target_query_count(max_rounds)
        prompt = (
            f"Given the debate topic: '{topic}'\n"
            f"Generate exactly {query_count} distinct search queries covering empirical statistics, "
            f"economic/social impacts, studies, and unintended consequences.\n"
            f"Output ONLY the queries, one per line, with no commentary."
        )
        response = ollama_client.generate(prompt, temperature=0.3)
        queries = [q.strip().lstrip("0123456789.- ") for q in response.splitlines() if q.strip()]
        return queries[:query_count] or [f"{topic} empirical evidence", f"{topic} statistics analysis"]

    def extract_evidence(self, topic: str, article_text: str, source_url: str) -> List[EvidenceUnit]:
        prompt = (
            f"Topic: '{topic}'\n"
            f"Article URL: {source_url}\n"
            f"Article Text Excerpt:\n{article_text}\n\n"
            f"Extract up to 4 discrete factual claims, empirical findings, or statistics.\n"
            f"Format strictly as JSON with keys:\n"
            f"- 'claim_text': concise factual assertion\n"
            f"- 'quote': verbatim or precise extract\n"
            f"- 'status': 'SUPPORTED' or 'CONTRADICTED'\n\n"
            f"Output a valid JSON list of objects: [{{\"claim_text\": \"...\", \"quote\": \"...\", \"status\": \"SUPPORTED\"}}]"
        )
        try:
            raw_json = ollama_client.generate_json(prompt)
            items = []
            if isinstance(raw_json, list):
                for item in raw_json:
                    items.append(EvidenceUnit(
                        evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                        claim_text=item.get("claim_text", ""),
                        quote=item.get("quote", ""),
                        source_url=source_url,
                        publisher=source_url.split("/")[2] if "//" in source_url else source_url,
                        evidence_score=0.85,
                        status=item.get("status", "SUPPORTED")
                    ))
            return items
        except Exception as e:
            logger.warning(f"Evidence extraction parsing failed: {e}")
            return []

    async def execute_research_pipeline(self, topic: str, max_rounds: int = 2) -> int:
        if hasattr(chroma_client, "flush_collection"):
            chroma_client.flush_collection()

        sub_queries = self.generate_sub_queries(topic, max_rounds)
        logger.info(f"[Research Agent] Generated {len(sub_queries)} queries for {max_rounds} rounds.")

        all_urls = []
        for q in sub_queries:
            urls = search_service.search_urls(q, limit=2)
            all_urls.extend(urls)
        
        unique_urls = list(dict.fromkeys(all_urls))[:6]
        scraped_docs = await self._parallel_scrape(unique_urls)

        all_evidence: List[EvidenceUnit] = []
        for doc in scraped_docs:
            facts = self.extract_evidence(topic, doc["text"], doc["url"])
            all_evidence.extend(facts)

        if all_evidence and hasattr(chroma_client, "batch_insert_evidence"):
            chroma_client.batch_insert_evidence(all_evidence)

        logger.info(f"[Research Agent] Indexed {len(all_evidence)} discrete EvidenceUnits into ChromaDB.")
        return len(all_evidence)

research_agent = ResearchAgent()
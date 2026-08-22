import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from ddgs import DDGS
import trafilatura

from schemas.evidence_schema import SourceMetadata

logger = logging.getLogger(__name__)

class WebSearchService:
    """Keyless dynamic web search & webpage scraper."""

    def __init__(self):
        self.ddgs = DDGS()

    def search_topic(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web for a query and return title, URL, and snippet."""
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": res.get("title", ""),
                    "url": res.get("href", ""),
                    "snippet": res.get("body", ""),
                }
                for res in results
                if res.get("href")
            ]
        except Exception as e:
            logger.error(f"Error during search for query '{query}': {e}")
            return []

    def scrape_url_content(self, url: str) -> Optional[str]:
        """Fetch and extract clean plain text from a URL using Trafilatura."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            extracted_text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            return extracted_text
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return None

    def evaluate_source_metadata(self, url: str, title: str) -> SourceMetadata:
        """Dynamically evaluate domain credibility heuristics without static whitelists."""
        domain = urlparse(url).netloc.lower()
        
        is_edu_gov = domain.endswith(".edu") or domain.endswith(".gov") or domain.endswith(".org")
        is_academic = "doi.org" in domain or "arxiv.org" in domain or "sciencedirect" in domain or "nih.gov" in domain
        
        flags = []
        credibility_score = 0.6  # Baseline
        
        if is_academic:
            credibility_score = 0.95
            flags.append("ACADEMIC_PEER_REVIEWED")
        elif is_edu_gov:
            credibility_score = 0.85
            flags.append("INSTITUTIONAL_SOURCE")
        elif "wikipedia.org" in domain:
            credibility_score = 0.50
            flags.append("TERTIARY_ENCYCLOPEDIA")
        else:
            flags.append("GENERAL_WEB_SOURCE")

        return SourceMetadata(
            url=url,
            title=title,
            domain=domain,
            publisher=domain,
            is_primary_source=is_academic or is_edu_gov,
            credibility_score=credibility_score,
            validation_flags=flags
        )

search_service = WebSearchService()
import logging
import os
from typing import List, Optional
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from config.settings import settings
from schemas.evidence_schema import EvidenceUnit

logger = logging.getLogger(__name__)


class ChromaEvidenceStore:
    """Manages vector storage and semantic retrieval of atomic debate evidence."""

    def __init__(self):
        self.collection_name = getattr(
            settings,
            "COLLECTION_NAME",
            getattr(settings, "CHROMA_COLLECTION_NAME", "debate_curated_evidence"),
        )
        self.persist_dir = getattr(
            settings,
            "PERSIST_DIRECTORY",
            getattr(settings, "CHROMA_PERSIST_DIR", "./data/chroma_db"),
        )
        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Pull model configuration gracefully from settings
        embed_model = getattr(settings, "EMBEDDING_MODEL", getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text"))
        ollama_base = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

        self.embeddings = OllamaEmbeddings(
            model=embed_model,
            base_url=ollama_base
        )
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    def reset_evidence_collection(self):
        """Flushes the collection for a fresh debate session to avoid contradictory cross-pollution."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        logger.info("[ChromaDB] Evidence collection flushed for new session.")

    # Compatibility alias for research agent calls
    def flush_collection(self):
        self.reset_evidence_collection()

    def add_evidence_units(self, evidence_units: List[EvidenceUnit]):
        """Converts structured EvidenceUnits into LangChain Documents and indexes them in batch."""
        if not evidence_units:
            return

        documents = []
        for unit in evidence_units:
            # Page content combines claim and verbatim quote for dense retrieval coverage
            content = f"Claim: {unit.claim_text}\nQuote: {unit.quote}"
            
            doc = Document(
                page_content=content,
                metadata={
                    "evidence_id": unit.evidence_id or "",
                    "claim_text": unit.claim_text or "",
                    "source_url": unit.source_url or "",
                    "publisher": unit.publisher or "Web Source",
                    "evidence_score": float(unit.evidence_score or 0.8),
                    "status": str(unit.status or "SUPPORTED"),
                },
            )
            documents.append(doc)

        try:
            if documents:
                self.vectorstore.add_documents(documents)
                logger.info(f"[ChromaDB] Successfully indexed {len(documents)} evidence units.")
        except Exception as e:
            logger.error(f"[ChromaDB] Batch insertion error: {e}")

    # Compatibility alias for batch insertion
    def batch_insert_evidence(self, evidence_units: List[EvidenceUnit]):
        self.add_evidence_units(evidence_units)

    def search_evidence(self, query: str, k: int = 3) -> List[Document]:
        """Performs semantic similarity search over stored debate evidence."""
        try:
            return self.vectorstore.similarity_search(query, k=k)
        except Exception as e:
            logger.warning(f"[ChromaDB] Semantic similarity search failed: {e}")
            return []


# Export both instance names for compatibility across agents & graph nodes
evidence_store = ChromaEvidenceStore()
chroma_client = evidence_store
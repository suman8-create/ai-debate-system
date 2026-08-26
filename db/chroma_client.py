import logging
import os
from typing import List
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
    # Matches your settings.py COLLECTION_NAME
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
    self.embeddings = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL, base_url=settings.OLLAMA_BASE_URL
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
    print("[ChromaDB] Evidence collection flushed for new session.")

  def add_evidence_units(self, evidence_units: List[EvidenceUnit]):
    """Converts structured EvidenceUnits into LangChain Documents and indexes them."""
    documents = []
    for unit in evidence_units:
      doc = Document(
          page_content=unit.quote,
          metadata={
              "claim_text": unit.claim_text,
              "source_url": unit.source_url,
              "publisher": unit.publisher,
              "evidence_score": unit.evidence_score,
              "status": unit.status,
          },
      )
      documents.append(doc)

    if documents:
      self.vectorstore.add_documents(documents)

  def search_evidence(self, query: str, k: int = 3) -> List[Document]:
    """Performs semantic similarity search over stored debate evidence."""
    try:
      return self.vectorstore.similarity_search(query, k=k)
    except Exception as e:
      logger.warning(f"ChromaDB search failed: {e}")
      return []


evidence_store = ChromaEvidenceStore()
import logging
from typing import List, Dict, Any, Optional
import chromadb
from schemas.evidence_schema import AtomicEvidence

logger = logging.getLogger(__name__)

class VectorDBService:
    """Manages persistent ChromaDB vector storage and semantic evidence search."""

    def __init__(self, collection_name: str = "debate_evidence"):
        self.client = chromadb.Client()
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def flush_collection(self):
        """Clears existing evidence vectors for a fresh debate session."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info("[ChromaDB] Evidence collection flushed for new session.")
        except Exception as e:
            logger.warning(f"Error resetting ChromaDB collection: {e}")

    def batch_insert_evidence(self, evidence_list: List[AtomicEvidence]):
        """Batches multiple atomic evidence chunks into ChromaDB at once."""
        if not evidence_list or not self.collection:
            return

        ids = [f"ev_{i}_{abs(hash(e.claim)) % 100000}" for i, e in enumerate(evidence_list)]
        documents = [f"{e.claim} | {e.quote}" for e in evidence_list]
        metadatas = [
            {
                "source_url": e.source_url or "",
                "publisher": e.publisher or "",
                "polarity": str(e.polarity or "NEUTRAL"),
                "credibility": float(e.credibility_score or 0.85)
            }
            for e in evidence_list
        ]

        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"[ChromaDB] Inserted {len(documents)} evidence nodes.")
        except Exception as e:
            logger.error(f"Failed batch inserting into ChromaDB: {e}")

    def search_evidence(self, query: str, n_results: int = 3, polarity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves top-k semantically relevant evidence passages."""
        if not self.collection:
            return []
        try:
            where_filter = {"polarity": polarity} if polarity else None
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )

            records = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                for doc, meta in zip(docs, metas):
                    records.append({
                        "text": doc,
                        "metadata": meta
                    })
            return records
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []

vector_service = VectorDBService()
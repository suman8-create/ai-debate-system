import os
from typing import List, Dict, Any, Optional
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config.settings import settings
from schemas.evidence_schema import EvidenceUnit

class ChromaEvidenceStore:
    """Persistent ChromaDB Vector Store client powered by local Ollama embeddings."""
    
    def __init__(
        self,
        collection_name: str = settings.COLLECTION_NAME,
        persist_dir: str = settings.CHROMA_PERSIST_DIR
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        
        # 1. Initialize local Ollama embedding model
        self.embedding_function = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # 2. Instantiate Persistent Chroma Vector Store
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_dir
        )

    def add_evidence_units(self, evidence_list: List[EvidenceUnit]) -> List[str]:
        """Store atomic evidence records with provenance metadata in ChromaDB."""
        if not evidence_list:
            return []
        
        documents = []
        ids = []
        
        for item in evidence_list:
            # Metadata dictionary for Chroma filtering and audit tracing
            metadata: Dict[str, Any] = {
                "evidence_id": item.evidence_id,
                "source_url": item.source_url,
                "publisher": item.publisher or "Unknown",
                "author": item.author or "Unknown",
                "publication_year": item.publication_year or 0,
                "evidence_score": float(item.evidence_score),
                "status": item.status,
                "created_at": item.created_at
            }
            
            # The text embedded and searched over combines the factual claim and exact quote
            content = f"Claim: {item.claim_text}\nQuote: {item.quote}"
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
            ids.append(item.evidence_id)
            
        self.vector_store.add_documents(documents=documents, ids=ids)
        return ids

    def search_evidence(
        self,
        query: str,
        k: int = 4,
        min_score: Optional[float] = None
    ) -> List[Document]:
        """Retrieve the top-k most relevant evidence documents for a given query."""
        results = self.vector_store.similarity_search(query=query, k=k)
        
        if min_score is not None:
            results = [
                doc for doc in results 
                if doc.metadata.get("evidence_score", 0.0) >= min_score
            ]
            
        return results

    def clear_evidence_base(self):
        """Reset/clear collection for fresh debate topics if needed."""
        self.vector_store.reset_collection()

evidence_store = ChromaEvidenceStore()
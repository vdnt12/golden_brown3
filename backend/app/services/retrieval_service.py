from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.services.vector_service import vector_service
from app.core.logging import log_event

class RetrievalService:
    @classmethod
    def retrieve_context(
        cls,
        document_id: str,
        question: str,
        top_k: int = 5,
        threshold: float = 0.35,
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Section 14 & 15: Retrieve top K chunks, filter by similarity threshold, construct context.

        Returns:
            (filtered_chunks, formatted_context_str, has_relevant_information)
        """
        log_event("QUERY", question)
        raw_hits = vector_service.query(document_id, question, top_k=top_k)
        log_event("RETRIEVAL", f"Retrieved chunks: {len(raw_hits)}")

        if not raw_hits:
            return [], "", False

        best_similarity = max((h["similarity"] for h in raw_hits), default=0.0)
        log_event("RELEVANCE", f"Best similarity: {best_similarity:.2f}")

        # Section 15: Check relevance threshold and keyword overlap
        q_tokens = set(question.lower().split())
        # Filter out common stop words
        stop_words = {"what", "is", "the", "of", "and", "a", "an", "in", "on", "for", "to", "who", "when", "where", "how", "why", "it", "this", "that"}
        meaningful_tokens = q_tokens - stop_words

        filtered_chunks: List[Dict[str, Any]] = []
        for hit in raw_hits:
            hit_text_lower = hit["text"].lower()
            # If hit has token overlap or passes similarity threshold
            has_keyword_match = any(token in hit_text_lower for token in meaningful_tokens)
            if hit["similarity"] >= threshold or has_keyword_match:
                filtered_chunks.append(hit)

        if not filtered_chunks or (best_similarity < threshold and not any(any(t in h["text"].lower() for t in meaningful_tokens) for h in raw_hits)):
            return [], "", False

        # Format context string
        context_parts = []
        for i, chunk in enumerate(filtered_chunks, 1):
            page_info = f" (Page {chunk['page']})" if chunk.get("page") else ""
            context_parts.append(f"[Excerpt {i}{page_info}]\n{chunk['text']}")

        formatted_context = "\n\n".join(context_parts)
        return filtered_chunks, formatted_context, True

retrieval_service = RetrievalService()

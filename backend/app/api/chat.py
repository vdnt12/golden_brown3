from fastapi import APIRouter, HTTPException, status
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.services.document_service import document_service
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.config import settings
from app.prompts.rag_prompt import NO_INFO_FALLBACK

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat_with_document(request: ChatRequest):
    """Section 14 & 25: POST /api/chat."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Verify document exists and is ready
    doc = document_service.get_document(request.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status == "processing":
        raise HTTPException(
            status_code=400,
            detail="Please wait until the document has finished processing."
        )
    if doc.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Document processing failed: {doc.error}"
        )

    # Section 1 & 14: Intent Classification (Document Summarization vs Question Answering)
    from app.services.intent_service import IntentClassifier, QueryIntent
    from app.services.summarization_service import summarization_service
    from app.services.vector_service import vector_service

    intent = IntentClassifier.classify(request.question)
    if intent == QueryIntent.SUMMARY:
        # Full Document Summarization Pipeline: ALL chunks participate
        summary_result = summarization_service.summarize_document(request.document_id)
        if summary_result.get("status") == "error":
            return ChatResponse(
                answer="Unable to generate document summary. Please verify the document has readable text.",
                sources=[],
            )

        all_chunks = vector_service.get_all_chunks(request.document_id)
        sources: list[ChatSource] = []
        seen_chunks = set()
        for chunk in all_chunks:
            if chunk["chunk_id"] not in seen_chunks:
                sources.append(
                    ChatSource(
                        filename=chunk.get("filename") or doc.filename,
                        page=chunk.get("page"),
                        chunk_id=chunk["chunk_id"],
                    )
                )
                seen_chunks.add(chunk["chunk_id"])

        return ChatResponse(
            answer=summary_result["summary"],
            sources=sources,
        )

    # 2. Retrieve top K chunks & check relevance threshold (Section 14 & 15)
    filtered_chunks, context, has_relevant = retrieval_service.retrieve_context(
        document_id=request.document_id,
        question=request.question,
        top_k=settings.TOP_K,
        threshold=settings.SIMILARITY_THRESHOLD,
    )

    if not has_relevant or not filtered_chunks:
        # Section 15: Return "I couldn't find that information in the uploaded document."
        return ChatResponse(
            answer=NO_INFO_FALLBACK,
            sources=[],
        )

    # 3. Generate grounded answer
    answer = llm_service.generate_answer(
        question=request.question,
        retrieved_context=context,
        conversation=request.conversation,
    )

    # 4. Construct sources (Section 18)
    sources: list[ChatSource] = []
    if answer != NO_INFO_FALLBACK:
        seen_chunks = set()
        for chunk in filtered_chunks:
            if chunk["chunk_id"] not in seen_chunks:
                sources.append(
                    ChatSource(
                        filename=chunk.get("filename") or doc.filename,
                        page=chunk.get("page"),
                        chunk_id=chunk["chunk_id"],
                    )
                )
                seen_chunks.add(chunk["chunk_id"])

    return ChatResponse(
        answer=answer,
        sources=sources,
    )

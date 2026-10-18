import re
from typing import List, Optional
from app.models.document import ExtractedPage, DocumentChunk
from app.core.config import settings
from app.core.logging import log_event

class ChunkingService:
    @classmethod
    def split_into_semantic_blocks(cls, text: str) -> List[str]:
        """Split text at natural boundaries (paragraphs, bullet points, numbered lists)."""
        paragraphs = text.split("\n\n")
        blocks: List[str] = []
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            # If paragraph is unusually long, further split into sentences
            if len(p_strip) > settings.CHUNK_SIZE * 3:
                sentences = re.split(r"(?<=[.!?])\s+", p_strip)
                blocks.extend([s.strip() for s in sentences if s.strip()])
            else:
                blocks.append(p_strip)
        return blocks

    @classmethod
    def chunk_pages(
        cls,
        pages: List[ExtractedPage],
        document_id: str,
        filename: str,
        chunk_char_size: Optional[int] = None,
        overlap_chars: Optional[int] = None,
    ) -> List[DocumentChunk]:
        """Section 8: Create semantic chunks preserving document ID, filename, page, chunk ID."""
        target_size = chunk_char_size or (settings.CHUNK_SIZE * 3)  # approx 700-1000 tokens in characters
        overlap = overlap_chars or (settings.CHUNK_OVERLAP * 3)

        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for page in pages:
            if not page.text.strip():
                continue

            blocks = cls.split_into_semantic_blocks(page.text)
            current_chunk_blocks: List[str] = []
            current_length = 0

            for block in blocks:
                block_len = len(block)
                if current_length + block_len > target_size and current_chunk_blocks:
                    # Form a chunk
                    chunk_text = "\n\n".join(current_chunk_blocks).strip()
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{document_id}_{chunk_idx}",
                            document_id=document_id,
                            filename=filename,
                            page=page.page_number,
                            chunk_index=chunk_idx,
                            text=chunk_text,
                        )
                    )
                    chunk_idx += 1

                    # Retain overlap from previous blocks if possible
                    overlap_blocks: List[str] = []
                    overlap_len = 0
                    for b in reversed(current_chunk_blocks):
                        if overlap_len + len(b) <= overlap:
                            overlap_blocks.insert(0, b)
                            overlap_len += len(b)
                        else:
                            break
                    current_chunk_blocks = overlap_blocks
                    current_length = overlap_len

                current_chunk_blocks.append(block)
                current_length += block_len

            if current_chunk_blocks:
                chunk_text = "\n\n".join(current_chunk_blocks).strip()
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}_{chunk_idx}",
                        document_id=document_id,
                        filename=filename,
                        page=page.page_number,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                    )
                )
                chunk_idx += 1

        log_event("CHUNKING", f"Chunks created: {len(chunks)}")
        return chunks

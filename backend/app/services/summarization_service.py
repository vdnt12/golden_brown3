import re
from typing import List, Dict, Any, Optional
from app.services.vector_service import vector_service
from app.services.document_service import document_service
from app.services.llm_service import llm_service
from app.core.logging import log_event

INTERMEDIATE_PROMPT_TEMPLATE = """You are summarizing part of a document.

Summarize ONLY the information contained in the provided document text.

Preserve important factual information.

Pay special attention to:
- names
- people
- organizations
- dates
- amounts
- prices
- bills
- account numbers
- addresses
- deadlines
- obligations
- important conditions
- important events
- important clauses
- decisions
- conclusions
- warnings

Do not add information that is not present.
Do not use outside knowledge.

Document section:
{chunk_text}

Create a factual intermediate summary."""

FINAL_PROMPT_TEMPLATE = """You are creating the final summary of a document.

The following text contains summaries of ALL sections of the document.

Create a complete and accurate summary using ONLY this information.

Include the most important facts.

Preserve:
- names
- organizations
- dates
- numbers
- monetary amounts
- addresses
- deadlines
- obligations
- important terms
- important events
- conclusions
- important warnings

Do not invent information.
Do not use outside knowledge.
Do not omit important information merely because it appeared in an earlier section.

Organize the result clearly.
Use headings and bullet points where useful.

DOCUMENT SUMMARIES:
{combined_summaries}

FINAL SUMMARY:"""

class DocumentSummarizationService:
    def __init__(self, batch_size: int = 8):
        self.batch_size = batch_size

    def summarize_document(self, document_id: str) -> Dict[str, Any]:
        """Section 2, 4, 5: Full document hierarchical summarization pipeline."""
        log_event("QUERY", f"Starting full document summarization for {document_id}")

        meta = document_service.get_document(document_id)
        # 1. Retrieve ALL chunks strictly for this document (Section 5, 20, 21)
        chunks = vector_service.get_all_chunks(document_id)
        if not chunks:
            log_event("STATUS", f"Summarization failed: No chunks found for {document_id}")
            return {
                "document_id": document_id,
                "status": "error",
                "message": "Unable to generate document summary. No document content available.",
                "summary": "",
            }

        filename = meta.filename if meta else (chunks[0].get("filename") or "document")
        log_event("RETRIEVAL", f"Retrieved ALL {len(chunks)} chunks for full document summarization")

        # 2. Chunk grouping (Section 6)
        batches: List[List[Dict[str, Any]]] = []
        for i in range(0, len(chunks), self.batch_size):
            batches.append(chunks[i : i + self.batch_size])

        # 3. Generate intermediate summaries (Section 7)
        intermediate_summaries: List[str] = []
        for idx, batch in enumerate(batches):
            batch_text = "\n\n".join(c["text"] for c in batch)
            log_event("LLM", f"Summarizing batch {idx + 1} of {len(batches)} ({len(batch)} chunks)")
            
            summary = self._summarize_batch(batch_text, batch_num=idx + 1, total_batches=len(batches))
            intermediate_summaries.append(summary)

        # 4. Hierarchical combination if there are multiple levels (Section 17)
        current_level_summaries = intermediate_summaries
        while len(current_level_summaries) > 8:
            next_level: List[str] = []
            for i in range(0, len(current_level_summaries), self.batch_size):
                sub_group = current_level_summaries[i : i + self.batch_size]
                combined_sub = "\n\n---\n\n".join(sub_group)
                sub_summary = self._summarize_batch(combined_sub, batch_num=1, total_batches=1)
                next_level.append(sub_summary)
            current_level_summaries = next_level

        # 5. Final summary generation (Section 8, 9, 10, 11)
        combined_summaries_text = "\n\n---\n\n".join(
            f"### Section Summary {i + 1}\n{s}" for i, s in enumerate(current_level_summaries)
        )
        
        log_event("LLM", "Generating final document summary")
        final_summary = self._generate_final_summary(combined_summaries_text, filename, chunks)

        log_event("RESPONSE", f"Full document summary completed for {document_id}")
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "complete",
            "summary": final_summary,
            "total_chunks_processed": len(chunks),
        }

    def _summarize_batch(self, batch_text: str, batch_num: int, total_batches: int) -> str:
        """Generate intermediate summary for a chunk batch using LLM or deterministic fallback."""
        prompt = INTERMEDIATE_PROMPT_TEMPLATE.format(chunk_text=batch_text)
        messages = [
            {"role": "system", "content": "You are a factual document summarizer. Preserve numbers, names, dates, amounts, and critical obligations."},
            {"role": "user", "content": prompt},
        ]

        llm_resp = llm_service.generate_raw(messages)
        if llm_resp and len(llm_resp.strip()) > 30:
            return llm_resp.strip()

        # Deterministic grounded fallback extraction for intermediate batch
        return self._deterministic_extract_batch(batch_text)

    def _generate_final_summary(
        self, combined_summaries: str, filename: str, all_chunks: List[Dict[str, Any]]
    ) -> str:
        """Generate formatted final summary adhering to Sections 9, 10, 11, 18."""
        prompt = FINAL_PROMPT_TEMPLATE.format(combined_summaries=combined_summaries)
        messages = [
            {"role": "system", "content": "You are a professional document analysis and summarization system. Synthesize a clean, structured markdown summary preserving all facts, numbers, dates, and names."},
            {"role": "user", "content": prompt},
        ]

        llm_resp = llm_service.generate_raw(messages)
        if llm_resp and len(llm_resp.strip()) > 50:
            return llm_resp.strip()

        # Deterministic grounded synthesizer (100% offline, preserving all facts per Section 9, 10, 11, 18, 22)
        full_text = "\n\n".join(c["text"] for c in all_chunks)
        return self._deterministic_final_synthesizer(full_text, filename)

    def _deterministic_extract_batch(self, text: str) -> str:
        """Extract factual key-value pairs, dates, amounts, and substantive sentences."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        extracted_facts: List[str] = []

        for line in lines:
            if ":" in line:
                key, _, val = line.partition(":")
                if len(key.strip()) < 50 and val.strip():
                    extracted_facts.append(f"- **{key.strip()}**: {val.strip()}")
            elif any(sym in line for sym in ["₹", "$", "€", "units", "days", "notice", "due date", "bill", "rent"]):
                extracted_facts.append(f"- {line}")
            elif len(line.split()) >= 6 and not line.startswith("[Excerpt") and not line.startswith("Page"):
                extracted_facts.append(f"- {line}")

        return "\n".join(extracted_facts) if extracted_facts else text[:500]

    def _deterministic_final_synthesizer(self, full_text: str, filename: str) -> str:
        """Generate structured markdown summary meeting Sections 9, 10, 11, 18, 22."""
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]

        key_facts: Dict[str, str] = {}
        important_details: List[str] = []
        financial_info: List[str] = []
        dates_info: List[str] = []

        for line in lines:
            if ":" in line:
                key, _, val = line.partition(":")
                k_clean = key.strip()
                v_clean = val.strip()
                if len(k_clean) < 45 and v_clean and not k_clean.lower().startswith("section"):
                    key_facts[k_clean] = v_clean
                    continue

            # Check financial details
            if any(sym in line for sym in ["₹", "$", "€", "rent", "fee", "amount", "charge", "inr"]):
                financial_info.append(line)
            # Check dates / deadlines
            elif any(d in line.lower() for d in ["due date", "deadline", "period", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "2024", "2025", "2026"]):
                dates_info.append(line)
            elif len(line.split()) >= 5 and not line.startswith("[Excerpt") and not line.startswith("Page"):
                if not any(line in d for d in important_details):
                    important_details.append(line)

        # Detect document flavor
        is_bill = any(b in full_text.lower() for b in ["bill", "account number", "consumption", "units", "electricity", "utility"])
        is_contract = any(c in full_text.lower() for c in ["lease", "agreement", "contract", "parties", "clause", "tenant", "landlord", "termination"])

        if is_bill:
            title = "# Electricity Bill Summary" if "electricity" in full_text.lower() else "# Utility Bill Summary"
        elif is_contract:
            title = "# Contract Summary"
        else:
            title = "# Document Summary"

        output_sections: List[str] = [title, ""]

        # Overview
        output_sections.append("## Overview")
        if is_bill:
            consumer = key_facts.get("Consumer") or key_facts.get("Owner") or key_facts.get("Company") or "the account holder"
            output_sections.append(f"This document is a utility statement for {consumer}.")
        elif is_contract:
            output_sections.append("This document outlines the legal terms, conditions, and obligations governing the agreement.")
        else:
            output_sections.append(f"This document contains verified administrative, commercial, and operational information for {filename}.")
        output_sections.append("")

        # Key Information
        if key_facts:
            output_sections.append("## Key Information")
            for k, v in key_facts.items():
                output_sections.append(f"- **{k}**: {v}")
            output_sections.append("")

        # Financial Information
        if financial_info:
            output_sections.append("## Financial Information")
            for f in financial_info:
                output_sections.append(f"- {f}")
            output_sections.append("")

        # Important Dates / Deadlines
        if dates_info:
            output_sections.append("## Important Dates & Periods")
            for d in dates_info:
                output_sections.append(f"- {d}")
            output_sections.append("")

        # Important Details / Conditions
        if important_details:
            output_sections.append("## Important Details & Provisions")
            for det in important_details:
                output_sections.append(f"- {det}")
            output_sections.append("")

        # Conclusion / Notice
        output_sections.append("## Summary Notes")
        output_sections.append(f"All facts above are directly extracted from `{filename}` without external assumptions.")

        return "\n".join(output_sections)

summarization_service = DocumentSummarizationService()

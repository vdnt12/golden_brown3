import re
from pathlib import Path
from typing import List
import pymupdf  # PyMuPDF
from app.models.document import ExtractedPage
from app.core.logging import log_event

class ExtractionError(Exception):
    pass

class ExtractionService:
    @staticmethod
    def clean_text(text: str) -> str:
        """Section 7: Clean text while preserving headings, paragraphs, lists, and structure."""
        if not text:
            return ""
        # Replace carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace non-breaking spaces and unusual whitespace
        text = re.sub(r"[ \t]+", " ", text)
        # Normalize repeated newlines (more than 2 to 2)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip trailing/leading spaces on lines
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    @classmethod
    def extract_pdf(cls, file_path: Path) -> List[ExtractedPage]:
        """Section 5: Extract text from PDF using PyMuPDF with OCR fallback."""
        try:
            doc = pymupdf.open(str(file_path))
        except Exception as exc:
            raise ExtractionError(f"Failed to open PDF file: {exc}") from exc

        if len(doc) == 0:
            raise ExtractionError("The uploaded PDF is empty.")

        pages: List[ExtractedPage] = []
        total_extracted_chars = 0

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_text = page.get_text() or ""
            is_ocr = False

            # Check if text is little or missing (scanned image page)
            if len(page_text.strip()) < 30:
                try:
                    # Attempt OCR on the page via PyMuPDF pixmap OCR if available
                    pix = page.get_pixmap()
                    ocr_pdf_bytes = page.get_textpage_ocr(language="eng").extractText()
                    if ocr_pdf_bytes and len(ocr_pdf_bytes.strip()) > len(page_text.strip()):
                        page_text = ocr_pdf_bytes
                        is_ocr = True
                        log_event("EXTRACTION", f"Page {page_num}: OCR activated successfully.")
                except Exception as ocr_err:
                    log_event("EXTRACTION", f"Page {page_num}: OCR fallback not available or failed: {ocr_err}")

            cleaned = cls.clean_text(page_text)
            total_extracted_chars += len(cleaned)
            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=cleaned,
                    is_ocr=is_ocr,
                )
            )

        doc.close()

        if total_extracted_chars == 0:
            raise ExtractionError("The PDF contains no readable text and OCR produced no characters.")

        log_event("EXTRACTION", f"Pages: {len(pages)} Characters: {total_extracted_chars}")
        return pages

    @classmethod
    def extract_txt(cls, file_path: Path) -> List[ExtractedPage]:
        """Section 6: Read TXT with UTF-8 and graceful encoding fallback."""
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        raw_text = None

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    raw_text = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if raw_text is None:
            raise ExtractionError("Unable to decode the TXT file with supported text encodings.")

        cleaned = cls.clean_text(raw_text)
        if not cleaned.strip():
            raise ExtractionError("The uploaded file is empty.")

        log_event("EXTRACTION", f"TXT file extracted. Characters: {len(cleaned)}")
        # TXT files represent page 1
        return [ExtractedPage(page_number=1, text=cleaned, is_ocr=False)]

    @classmethod
    def extract(cls, file_path: Path, filename: str) -> List[ExtractedPage]:
        """Extract document text based on file extension."""
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            return cls.extract_pdf(file_path)
        elif suffix == ".txt":
            return cls.extract_txt(file_path)
        else:
            raise ExtractionError("Unsupported file type. Please upload a PDF or TXT file.")

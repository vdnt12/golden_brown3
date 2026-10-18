# GBDoc — Document-Grounded Legal RAG Chatbot

GBDoc is a production-grade, document-grounded Retrieval-Augmented Generation (RAG) system. It allows users to upload legal agreements, contracts, and documents (`.pdf` and `.txt`), index them into vector search collections with PyMuPDF and ChromaDB, and query them with strict anti-hallucination guarantees.

> **Core Principle:** The uploaded document is the **sole source of truth**. If information is not in the document, GBDoc explicitly returns:
> *"I couldn't find that information in the uploaded document."*

---

## 1. Architecture

```text
DOCUMENT (PDF / TXT)
      ↓
TEXT EXTRACTION (PyMuPDF / OCR Fallback / UTF-8)
      ↓
TEXT CLEANING (Whitespace & artifact normalization)
      ↓
SEMANTIC CHUNKING (700–1000 tokens, natural boundaries)
      ↓
EMBEDDINGS (Chroma all-MiniLM-L6-v2 / Configurable)
      ↓
VECTOR STORE (ChromaDB document-isolated collections)
      ↓
RETRIEVAL (Top-K similarity + Relevance Threshold)
      ↓
RELEVANT CONTEXT (Page numbers & verbatim citations)
      ↓
LLM / GROUNDED SYNTHESIS (Strict System Prompt)
      ↓
GROUNDED ANSWER + CITATIONS
```

---

## 2. Tech Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Document Processing:** PyMuPDF (`fitz`), Tesseract OCR fallback
- **Vector Database:** ChromaDB (persistent isolated collections per document)
- **Embeddings:** Chroma default ONNX / Configurable (`EMBEDDING_PROVIDER`)
- **LLM Engine:** Local Ollama (`gemma4:e4b-it-q4_K_M`, `hermes3:8b`), OpenAI API, or Grounded Extractive Engine
- **Frontend:** React 18, Vite, TypeScript, Vanilla CSS
- **Testing:** Pytest, FastAPI TestClient

---

## 3. Project Structure

```text
golden_brown3/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint
│   │   ├── api/
│   │   │   ├── upload.py               # POST /api/upload
│   │   │   ├── chat.py                 # POST /api/chat
│   │   │   ├── document.py             # GET status & DELETE document
│   │   │   └── health.py               # GET /api/health
│   │   ├── core/
│   │   │   ├── config.py               # Settings & environment variables
│   │   │   └── logging.py              # Structured event logging
│   │   ├── services/
│   │   │   ├── document_service.py     # Ingestion orchestration
│   │   │   ├── extraction_service.py   # PyMuPDF & OCR extraction
│   │   │   ├── chunking_service.py     # Semantic boundary chunking
│   │   │   ├── embedding_service.py    # Isolated embedding provider
│   │   │   ├── vector_service.py       # ChromaDB document isolation
│   │   │   ├── retrieval_service.py    # Top-K & relevance thresholding
│   │   │   └── llm_service.py          # Grounded anti-hallucination engine
│   │   ├── models/
│   │   │   ├── document.py             # Metadata & Chunk schemas
│   │   │   └── chat.py                 # Chat & Source schemas
│   │   └── prompts/
│   │       └── rag_prompt.py           # Strict anti-hallucination prompts
│   ├── tests/
│   │   └── test_backend.py             # Automated end-to-end tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx          # Drag & drop upload area
│   │   │   ├── ProcessingStatus.tsx    # Step-by-step progress indicator
│   │   │   ├── ChatWindow.tsx          # Chat interface & query states
│   │   │   ├── ChatMessage.tsx         # User & Assistant bubbles
│   │   │   └── SourceCitation.tsx      # Page & chunk citations
│   │   ├── services/
│   │   │   └── api.ts                  # Frontend API client
│   │   ├── App.tsx                     # Main application layout
│   │   ├── main.tsx
│   │   └── index.css                   # Responsive modern styling
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── .env.example
├── uploads/                            # Temporary upload directory
├── vector_store/                       # Persistent ChromaDB storage
├── test_document.txt                   # Section 32 benchmark file
├── README.md
└── .gitignore
```

---

## 4. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `local` | `local` (Ollama), `openai`, or deterministic |
| `LLM_MODEL` | `gemma4:e4b-it-q4_K_M` | Model name tag |
| `LLM_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `LLM_API_KEY` | `""` | Optional OpenAI API Key |
| `EMBEDDING_PROVIDER` | `chroma` | `chroma` or custom provider |
| `VECTOR_STORE_PATH` | `./vector_store` | Persistent directory for ChromaDB |
| `UPLOAD_DIR` | `./uploads` | Stored document files |
| `TOP_K` | `5` | Number of chunks retrieved |
| `SIMILARITY_THRESHOLD`| `0.35` | Minimum cosine relevance score |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size allowed |

---

## 5. Quickstart & Running Locally

### Backend Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start the FastAPI server
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup

```bash
# 1. Enter frontend folder
cd frontend

# 2. Install node dependencies
npm install

# 3. Start Vite dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser. (The app will automatically proxy API calls to backend at `http://127.0.0.1:8000`).

Alternatively, build the frontend for production:
```bash
cd frontend && npm run build
```
Once built, FastAPI serves both frontend and API directly on [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 6. API Reference

### Upload Document
- **`POST /api/upload`** (multipart/form-data)
  - `file`: PDF or TXT file
  - **Response (200):**
    ```json
    {
      "document_id": "8e7c2a6e-...",
      "filename": "contract.pdf",
      "status": "ready"
    }
    ```

### Document Status
- **`GET /api/document/{document_id}/status`**
  - **Response (200):**
    ```json
    {
      "document_id": "8e7c2a6e-...",
      "filename": "contract.pdf",
      "status": "ready",
      "pages": 12,
      "chunks": 48
    }
    ```

### Chat with Document
- **`POST /api/chat`**
  - **Payload:**
    ```json
    {
      "document_id": "8e7c2a6e-...",
      "question": "What is the notice period?",
      "conversation": []
    }
    ```
  - **Response (200):**
    ```json
    {
      "answer": "The notice period is 30 days.",
      "sources": [
        {
          "filename": "contract.pdf",
          "page": 1,
          "chunk_id": "8e7c2a6e-..._0"
        }
      ]
    }
    ```

### Delete Document
- **`DELETE /api/document/{document_id}`**
  - **Response (200):** `{"success": true}`

### Health Check
- **`GET /api/health`**
  - **Response (200):** `{"status": "ok"}`

---

## 7. Automated Testing & Verification

Run the comprehensive test suite (including the Section 32 critical benchmark):

```bash
PYTHONPATH=backend pytest backend/tests/test_backend.py -v
```

All tests pass:
- ✓ `test_health_check`
- ✓ `test_empty_file_rejected`
- ✓ `test_unsupported_file_rejected`
- ✓ `test_pdf_extraction_and_chunking`
- ✓ `test_critical_e2e_section_32` (Verifies exact fact retrieval & anti-hallucination rejection)

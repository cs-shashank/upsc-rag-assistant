# UPSC Document Assistant (RAG System)

An AI-powered question answering system for UPSC study material built using Retrieval Augmented Generation (RAG).

## Demo

Ask any question from your UPSC PDF and get accurate answers with page citations — directly in the browser.

## Features

- 📄 Upload any UPSC PDF document
- 🤖 Ask questions in plain English
- 📌 Get accurate answers with page citations
- 💬 Conversation history — ask follow-up questions
- ⚡ MMR retrieval for diverse, high-quality results
- 🔒 Rate limiting (10 requests/minute)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (async) |
| RAG Pipeline | LangChain |
| Vector Database | ChromaDB |
| Embeddings | Google Gemini Embeddings |
| LLM | Gemini 2.5 Flash |
| PDF Parsing | PyMuPDF |
| Frontend | React + Vite |

## Project Structure

```
upsc-rag-assistant/
├── app.py              # FastAPI backend with /ask endpoint
├── rag_core.py         # RAG pipeline (embeddings, retriever, LLM)
├── ingest.py           # PDF ingestion and ChromaDB population
├── query.py            # Terminal-based query interface
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── frontend/           # React + Vite frontend
    └── src/
        └── App.jsx     # Main chat interface
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/cs-shashank/upsc-rag-assistant.git
cd upsc-rag-assistant
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Add your Gemini API key to .env
```

Get a free Gemini API key at: https://aistudio.google.com

### 4. Add your PDF
```
Place your PDF in the project root and rename it: document.pdf
```

### 5. Ingest the document
```bash
python ingest.py
```

### 6. Start the backend
```bash
uvicorn app:app --reload --port 8000
```

### 7. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 8. Open the app
Visit: http://localhost:5173

## API Reference

### `POST /ask`

Ask a question about the document.

**Request:**
```json
{
  "question": "Who founded the Self-Respect Movement?",
  "history": []
}
```

**Response:**
```json
{
  "question": "Who founded the Self-Respect Movement?",
  "answer": "**(a) Periyar E.V. Ramaswamy Naicker**\n\nPeriyar founded the Self-Respect Movement...",
  "source_pages": [7, 13, 24]
}
```

## Project Status

   ongoing
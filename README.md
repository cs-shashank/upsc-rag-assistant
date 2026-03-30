# UPSC Document Assistant (RAG System)

An AI-powered question answering system for UPSC study material built using Retrieval Augmented Generation (RAG).

## What it does

- Upload any UPSC PDF document
- Ask questions in plain English
- Get accurate answers with page citations

## Tech Stack

| Component | Purpose |
|-----------|---------|
| **LangChain** | RAG pipeline orchestration |
| **ChromaDB** | Local vector database |
| **Google Gemini** | Embeddings + LLM |
| **PyMuPDF** | PDF text extraction |

## How to Run

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your Gemini API key** in `ingest.py` and `query.py`

3. **Add your PDF** and rename it `document.pdf`

4. **Ingest the document**
   ```bash
   python ingest.py
   ```

5. **Ask questions**
   ```bash
   python query.py
   ```

## Project Status

🚧 **Ongoing** — Actively under development.

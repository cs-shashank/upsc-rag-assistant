# 🎯 UPSC RAG Assistant

> An intelligent AI-powered study assistant for UPSC exam preparation — upload any PDF and ask questions, get precise answers with page citations.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://reactjs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.4-1C3C3C?style=flat)](https://langchain.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Cloud%20Vector%20DB-00C3FF?style=flat)](https://pinecone.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-4285F4?style=flat&logo=google)](https://ai.google.dev/)

---

## 📖 Project Description

**UPSC RAG Assistant** is a full-stack AI application that lets students upload UPSC study material (PDFs) and interact with it through a smart conversational chatbot. It uses **Retrieval Augmented Generation (RAG)** to fetch only the most relevant chunks from your document and pass them to Google Gemini to generate highly accurate, cited answers.

Unlike a plain LLM chatbot, this assistant only answers from your uploaded document — so you get focused, reliable, exam-relevant answers with exact page references. It is particularly optimized for MCQ-based study material.

---

## ✨ Features

- 📄 **PDF Upload** — Upload any UPSC study material PDF directly from the UI
- 🧠 **RAG Pipeline** — Retrieves the most relevant context using MMR (Maximal Marginal Relevance) search
- 💬 **Conversational Memory** — Supports multi-turn conversations with follow-up questions
- 📌 **Page Citations** — Each answer comes with exact source page numbers from the document
- ☁️ **Persistent Vector Database** — Powered by **Pinecone** (cloud), so your knowledge base survives server restarts
- ⚡ **Rate Limiting** — Built-in API rate limiting (10 requests/minute) to prevent abuse
- 🌐 **React Frontend** — Modern, responsive chat interface built with Vite + React
- 🔒 **Secure** — API keys are stored as environment variables, never hardcoded

---

## 🛠️ Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python), Uvicorn |
| **Frontend** | React 18 + Vite, react-markdown |
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | Google `gemini-embedding-001` (3072 dims) |
| **Vector Store** | Pinecone (Serverless, AWS us-east-1) |
| **RAG Framework** | LangChain, langchain-pinecone |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Rate Limiting** | SlowAPI |
| **Config** | python-dotenv |

---

## 📁 Project Structure

```
upsc-rag-assistant/
├── app.py                 # FastAPI backend with /ask, /upload, /documents routes
├── rag_core.py            # Core RAG pipeline (embeddings, retriever, LLM)
├── ingest.py              # One-time script to embed & push PDFs to Pinecone
├── query.py               # CLI query utility (for testing)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Files excluded from git
└── frontend/              # React + Vite frontend
    ├── src/
    │   └── App.jsx        # Main chat UI component
    ├── package.json
    └── vite.config.js
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com/) API key
- A [Pinecone](https://pinecone.io/) account (free tier)

### 1. Clone the Repository
```bash
git clone https://github.com/cs-shashank/upsc-rag-assistant.git
cd upsc-rag-assistant
```

### 2. Set Up Environment Variables
```bash
# Copy the example env file
cp .env.example .env
```
Edit `.env` and fill in your keys:
```env
GOOGLE_API_KEY=your-gemini-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=upsc-rag
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Pinecone Index
Create a **Serverless** index on [app.pinecone.io](https://app.pinecone.io) with:
- **Dimensions**: `3072`
- **Metric**: `cosine`
- **Cloud / Region**: `AWS / us-east-1`

### 5. Ingest Your PDF
```bash
# Place your PDF in the project root as document.pdf
python ingest.py
```

### 6. Start the Backend
```bash
uvicorn app:app --reload
```
Backend runs on: `http://localhost:8000`

### 7. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on: `http://localhost:5173`

---

## 🚀 Usage

1. Open `http://localhost:5173` in your browser.
2. Type a question related to your uploaded document in the chat box.
3. The assistant retrieves relevant content, generates an answer, and cites the exact page numbers.
4. You can ask follow-up questions — the assistant remembers your conversation context.

You can also upload additional PDFs using the **Upload** button in the UI — they are embedded into Pinecone's cloud database automatically.

---

## 💡 Example Output

**User:** What is the correct answer to the question about the Soil Health Card Scheme?

**Assistant:**
> The correct answer is **(b) Ministry of Agriculture and Farmers' Welfare.**
> 
> The Soil Health Card Scheme is implemented by the Ministry of Agriculture and Farmers' Welfare to provide farmers with information about the nutrient status of their soil.
> 
> *Source: Pages 10, 11*

---

## 🎓 Purpose of the Project

This project was built to solve a real problem for UPSC aspirants — the inability to quickly query large study PDFs. Instead of manually flipping through 500+ pages, students can now ask natural-language questions and get precise, cited answers in seconds.

The RAG approach ensures the chatbot only answers from the provided study material, preventing the hallucinations common in plain LLM chatbots.

---

## 🔮 Future Improvements

- [ ] Multi-document support with namespace-based Pinecone separation
- [ ] User authentication and personal document libraries
- [ ] Subject-wise topic tagging and filtering
- [ ] Exam-style quiz generation from uploaded content
- [ ] Mobile-responsive PWA frontend
- [ ] Deploy backend on Render, frontend on Vercel

---

## 👨‍💻 Author

**Shashank Dwivedi**  
GitHub: [@cs-shashank](https://github.com/cs-shashank)

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).
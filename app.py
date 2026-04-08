import os
import shutil
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from rag_core import get_retriever, get_llm, get_embeddings, PROMPT_TEMPLATE

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploaded_docs")
UPLOAD_DIR.mkdir(exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
retriever = None
llm = None

# ── Startup / Shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever, llm
    print("Loading RAG pipeline...")
    retriever = get_retriever(search_type="mmr")
    llm = get_llm()
    print("✅ RAG pipeline ready!")
    yield
    print("Shutting down...")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="UPSC RAG API", version="2.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ── Models ────────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class QuestionRequest(BaseModel):
    question: str
    history: list[Message] = []

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def home():
    return {
        "status": "running",
        "message": "UPSC RAG API v2 is live!",
        "endpoints": {
            "POST /ask": "Ask a question about the document",
            "POST /upload": "Upload a new PDF document",
            "GET /documents": "List all uploaded documents",
        },
    }


@app.post("/ask")
@limiter.limit("10/minute")
async def ask(request: Request, body: QuestionRequest):
    """Ask a question. Supports conversation history for follow-up questions."""
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    history_text = ""
    for msg in body.history[-6:]:
        label = "User" if msg.role == "user" else "Assistant"
        history_text += f"{label}: {msg.content}\n"

    docs = await retriever.ainvoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "history", "question"],
    )
    final_prompt = prompt.format(
        context=context,
        history=history_text or "None",
        question=question,
    )
    response = await llm.ainvoke(final_prompt)
    pages = sorted({doc.metadata.get("page", 0) + 1 for doc in docs})

    answer_text = response.content
    if isinstance(answer_text, list):
        answer_text = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in answer_text)

    return {
        "question": question,
        "answer": answer_text,
        "source_pages": pages,
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and ingest it into ChromaDB.
    Supports multiple PDFs — each upload adds to the existing knowledge base.
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save the uploaded file
    save_path = UPLOAD_DIR / file.filename
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"📄 Saved: {file.filename}")

    try:
        # Load PDF
        loader = PyMuPDFLoader(str(save_path))
        documents = loader.load()
        print(f"   Loaded {len(documents)} pages")

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = splitter.split_documents(documents)
        print(f"   Split into {len(chunks)} chunks")

        # Embed and store in batches (Gemini free tier rate limit)
        embeddings = get_embeddings()
        batch_size = 50
        index_name = os.environ.get("PINECONE_INDEX_NAME", "upsc-rag")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            PineconeVectorStore.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=index_name
            )
            print(f"   Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")
            if i + batch_size < len(chunks):
                time.sleep(60)  # avoid Gemini rate limit

        print(f"✅ Ingested: {file.filename}")

        return {
            "message": f"Successfully ingested '{file.filename}'",
            "filename": file.filename,
            "pages": len(documents),
            "chunks": len(chunks),
        }

    except Exception as e:
        # Clean up saved file if ingestion fails
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all uploaded PDF documents."""
    files = sorted(UPLOAD_DIR.glob("*.pdf"))
    return {
        "documents": [f.name for f in files],
        "count": len(files),
    }
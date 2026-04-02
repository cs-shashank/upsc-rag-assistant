import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from rag_core import get_retriever, get_llm, PROMPT_TEMPLATE

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

retriever = None
llm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the RAG pipeline once when the server starts."""
    global retriever, llm
    print("Loading RAG pipeline …")
    retriever = get_retriever(search_type="mmr")
    llm = get_llm()
    print("✅ RAG pipeline ready!")
    yield
    print("Shutting down …")


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
    )

class Message(BaseModel):
    role: str   
    content: str

class QuestionRequest(BaseModel):
    question: str
    history: list[Message] = []
@app.get("/")
async def home():
    return {
        "status": "running",
        "message": "UPSC RAG API v2 is live!",
        "endpoints": {"POST /ask": "Ask a question about the document"},
    }


@app.post("/ask")
@limiter.limit("10/minute")
async def ask(request: Request, body: QuestionRequest):
    """
    Ask a question. Supports conversation history for follow-up questions.

    Request body:
    {
        "question": "Who founded the Self-Respect Movement?",
        "history": [
            {"role": "user",      "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
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

    return {
        "question": question,
        "answer": response.content,
        "source_pages": pages,
    }

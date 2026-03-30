# app.py — Flask API for the RAG pipeline
# Usage: python app.py
# Then send POST requests to http://localhost:5000/ask

from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

app = Flask(__name__)
CORS(app)  # allows React frontend to talk to this API

# ── CONFIG ──────────────────────────────────────────────────────────────────
DB_PATH        = "chroma_db"
GOOGLE_API_KEY = "your_api_key"   # same key as before
# ────────────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """
You are a helpful assistant answering questions from a UPSC study document.
Use the context below to answer the question. The document contains MCQ questions
with options (a), (b), (c), (d). Find the relevant question and identify the correct answer.

Context:
{context}

Question: {question}

Answer (mention the correct option and explain briefly, with page citation):
"""

# Load once when server starts — not on every request
print("Loading RAG pipeline...")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY
)
vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)
print("✅ RAG pipeline ready!")


def ask_question(question):
    """Core RAG logic — same as query.py but returns a dict"""
    # Step 1: retrieve relevant chunks
    docs = retriever.invoke(question)

    # Step 2: build context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Step 3: build prompt and ask LLM
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    final_prompt = prompt.format(context=context, question=question)
    response = llm.invoke(final_prompt)

    # Step 4: get source pages
    pages = sorted(set(
        doc.metadata.get("page", 0) + 1
        for doc in docs
    ))

    return {
        "answer": response.content,
        "source_pages": pages,
        "question": question
    }


# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Health check — visit http://localhost:5000 to confirm API is running"""
    return jsonify({
        "status": "running",
        "message": "UPSC RAG API is live!",
        "endpoints": {
            "POST /ask": "Ask a question about the document"
        }
    })


@app.route("/ask", methods=["POST"])
def ask():
    """
    Main endpoint — accepts a question, returns an answer
    
    Request body (JSON):
    {
        "question": "Who founded the Self-Respect Movement?"
    }
    
    Response (JSON):
    {
        "question": "...",
        "answer": "...",
        "source_pages": [12, 24]
    }
    """
    # Get question from request
    data = request.get_json()

    # Validate input
    if not data or "question" not in data:
        return jsonify({
            "error": "Please provide a question in the request body",
            "example": {"question": "Who founded the Self-Respect Movement?"}
        }), 400

    question = data["question"].strip()

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    # Get answer from RAG pipeline
    result = ask_question(question)
    return jsonify(result), 200


# ── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
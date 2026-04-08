import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

PROMPT_TEMPLATE = """
You are a helpful UPSC exam assistant. Use ONLY the context below to answer the question.
The document contains MCQ questions with options (a), (b), (c), (d).

Context:
{context}

Conversation History:
{history}

Question: {question}

Answer clearly — state the correct option in **bold**, give a brief explanation, and cite the page(s).
If the answer is not found in the context, say "I couldn't find this in the document."
"""

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

def get_vectorstore():
    index_name = os.environ.get("PINECONE_INDEX_NAME", "upsc-rag")
    return PineconeVectorStore(
        index_name=index_name,
        embedding=get_embeddings()
    )

def get_retriever(search_type: str = "mmr"):
    vectorstore = get_vectorstore()
    if search_type == "mmr":
        # MMR reduces redundant chunks and fetches more diverse results
        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.7}
        )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
        max_retries=2
    )

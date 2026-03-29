# query.py — Ask questions to your PDF in the terminal
# Usage: python query.py

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

# ── CONFIG ──────────────────────────────────────────────────────────────────
DB_PATH        = "chroma_db"
GOOGLE_API_KEY = "your-key-here" # same key as ingest.py
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
def load_chain():
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
    return retriever, llm

def ask(question, retriever, llm):
    # Step 1: retrieve relevant chunks
    docs = retriever.invoke(question)

    # Step 2: build context from chunks
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

    return response.content, pages

def main():
    print("🤖 RAG System Ready — ask anything about your document.")
    print("   Type 'quit' to exit.\n")

    retriever, llm = load_chain()

    while True:
        question = input("Your question: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        answer, pages = ask(question, retriever, llm)
        print("\n📌 Answer:")
        print(answer)
        print(f"\n📄 Sources: Page(s) {pages}\n")
        print("─" * 50)

if __name__ == "__main__":
    main()
import os
import re
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PDF_PATH = "document.pdf"
DB_PATH = "chroma_db"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Matches lines that start a new MCQ question: "1.", "2.", "Q1.", etc.
QUESTION_START = re.compile(r"(?m)^\s*(?:Q\.?\s*)?\d+[\.\)]\s+\w")


def chunk_by_questions(documents: list) -> list[Document]:
    """
    Split pages into question-aware chunks so that a question and its
    answer options always stay together — unlike fixed-character splitting.
    Falls back to the full page text when no MCQ structure is detected.
    """
    chunks: list[Document] = []

    for doc in documents:
        text = doc.page_content
        page = doc.metadata.get("page", 0)

        matches = list(QUESTION_START.finditer(text))

        if len(matches) < 2:
            # No clear MCQ pattern → keep the page as-is
            chunks.append(doc)
            continue

        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            snippet = text[start:end].strip()

            if len(snippet) > 50:          # skip very short noise
                chunks.append(Document(
                    page_content=snippet,
                    metadata={"page": page, "source": PDF_PATH},
                ))

    return chunks


def exponential_backoff(attempt: int, base: int = 5, cap: int = 120) -> None:
    wait = min(base * (2 ** attempt), cap)
    print(f"   Rate limited. Retrying in {wait}s …")
    time.sleep(wait)


def ingest() -> None:
    print(f"Loading PDF: {PDF_PATH}")
    loader = PyMuPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")

    print("Chunking by question boundaries …")
    chunks = chunk_by_questions(documents)
    print(f"Created {len(chunks)} question-aware chunks")

    print("Creating embeddings and saving to ChromaDB …")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )

    batch_size = 50
    vectorstore = None

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        attempt = 0

        while True:
            try:
                if vectorstore is None:
                    vectorstore = Chroma.from_documents(
                        documents=batch,
                        embedding=embeddings,
                        persist_directory=DB_PATH,
                    )
                else:
                    vectorstore.add_documents(batch)

                done = min(i + batch_size, len(chunks))
                print(f"   Processed {done}/{len(chunks)} chunks …")
                time.sleep(2)           # small polite delay between batches
                break

            except Exception as exc:
                err = str(exc).lower()
                if "429" in err or "quota" in err or "resource" in err:
                    exponential_backoff(attempt)
                    attempt += 1
                else:
                    raise

    print(f"✅ Done! {len(chunks)} chunks saved to '{DB_PATH}/'")
    print("   Now run: uvicorn app:app --reload")


if __name__ == "__main__":
    ingest()

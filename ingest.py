import os 
import time
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

PDF_PATH = "document.pdf"
DB_PATH = "chroma_db"
GOOGLE_API_KEY = "your-key-here"

def ingest():
    print(f"Loading PDF: {PDF_PATH}")
    loader = PyMuPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    print("Creating embeddings and saving to ChromaDB...")
    embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY
)

    # Process in batches of 50 to avoid rate limit
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        if i == 0:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=DB_PATH
            )
        else:
            vectorstore.add_documents(batch)
        print(f"   Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")
        time.sleep(60)  # wait 60 seconds between batches
    print(f"✅ Done! {len(chunks)} chunks saved to '{DB_PATH}/'")
    print("   Now run: python query.py")

if __name__ == "__main__":
    ingest()
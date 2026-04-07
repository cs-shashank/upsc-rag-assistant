import os
from dotenv import load_dotenv
from rag_core import get_llm

load_dotenv()

try:
    print(f"GOOGLE_API_KEY present: {bool(os.environ.get('GOOGLE_API_KEY'))}")
    llm = get_llm()
    print("LLM initialized successfully!")
except Exception as e:
    print(f"Error: {e}")

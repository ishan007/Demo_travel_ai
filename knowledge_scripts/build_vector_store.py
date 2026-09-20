"""Build the Chroma vector store from knowledge base documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag import build_vector_store

if __name__ == "__main__":
    print("Building vector store from knowledge base...")
    build_vector_store()
    print("Vector store built successfully.")
    
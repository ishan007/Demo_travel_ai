import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
MCP_SERVERS_DIR = BASE_DIR / "mcp_servers"
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GOOGLE_API_KEY = ""
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 5
KNOWLEDGE_SOURCES = {
    "wikivoyage_singapore.md": {
        "title": "Wikivoyage Singapore Travel Guide",
        "source_url": "https://en.wikivoyage.org/wiki/Singapore",
    },
    "visit_singapore_essential.md": {
        "title": "Visit Singapore Essential Travel Information",
        "source_url": "https://www.visitsingapore.com/travel-tips/essential-travel-information/",
    },
    "visit_singapore_itineraries.md": {
        "title": "Visit Singapore Sample Itineraries and Things To Do",
        "source_url": "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/",
    },
}

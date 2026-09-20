from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    KNOWLEDGE_DIR,
    KNOWLEDGE_SOURCES,
    TOP_K,
    VECTOR_STORE_DIR,
)


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def load_documents(knowledge_dir: Path = KNOWLEDGE_DIR) -> list:
    loader = DirectoryLoader(
        str(knowledge_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    for doc in docs:
        filename = Path(doc.metadata["source"]).name
        source = KNOWLEDGE_SOURCES.get(filename, {})
        doc.metadata["title"] = source.get("title", filename)
        doc.metadata["source_url"] = source.get("source_url", "")
    return docs


def load_vector_store() -> Chroma:
    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            f"Vector store not found at {VECTOR_STORE_DIR}. "
            "Run: python knowledge_scripts/build_vector_store.py"
        )
    return Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=get_embeddings(),
    )


def build_vector_store() -> Chroma:
    embeddings = get_embeddings()
    docs = load_documents()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n", " "],
    )
    chunks = splitter.split_documents(docs)

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_STORE_DIR),
    )


def retrieve(query: str, vector_store: Chroma, k: int = TOP_K) -> tuple[str, list[dict]]:
    results = vector_store.similarity_search_with_score(query, k=k)

    context_parts = []
    sources = []
    seen_titles = set()

    for doc, score in results:
        title = doc.metadata.get("title", "Unknown")
        url = doc.metadata.get("source_url", "")
        context_parts.append(doc.page_content)

        if title not in seen_titles:
            seen_titles.add(title)
            sources.append({"title": title, "url": url, "relevance": round(1 - score, 3)})

    context = "\n\n---\n\n".join(context_parts)
    return context, sources

# Singapore Travel Planning Assistant

A context-aware travel assistant that combines a document-based knowledge base (RAG) with live information from MCP tools (weather and currency conversion).

## Features

- **RAG Knowledge Base**: Semantic search over Singapore travel guides (Wikivoyage, Visit Singapore)
- **MCP Weather Tool**: Live forecasts via Open-Meteo API
- **MCP Currency Tool**: Live exchange rates via Frankfurter API
- **Combined Responses**: Weather-aware itineraries, budget planning with currency conversion
- **Multi-turn Chat**: Conversation context retained across turns
- **Source Citations**: Knowledge base sources displayed with each answer

## Tech Stack

| Component | Choice |
|-----------|--------|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | Chroma |
| Orchestration | LangChain + LangGraph |
| MCP Client | langchain-mcp-adapters |
| UI | Streamlit |

## Knowledge Base Sources

1. [Wikivoyage Singapore Travel Guide](https://en.wikivoyage.org/wiki/Singapore)
2. [Visit Singapore Essential Travel Information](https://www.visitsingapore.com/travel-tips/essential-travel-information/)
3. [Visit Singapore Sample Itineraries](https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/)

## Prompt Strategy

The system prompt instructs the model to:

1. **Use RAG context for destination facts** — attractions, transport, culture, itineraries. The prompt embeds retrieved chunks and source references directly.
2. **Use MCP tools only for current data** — weather forecasts and currency rates. The prompt explicitly forbids using MCP for destination knowledge.
3. **Label information types** — responses distinguish Knowledge Base facts, MCP tool results, and AI-generated suggestions.
4. **Avoid hallucination** — if retrieved content lacks an answer, the model must say so instead of inventing facts.
5. **Handle tool failures** — failed MCP calls must be reported, not replaced with fabricated data.
6. **Preserve conversation context** — prior user preferences (budget, family, dates) are passed in chat history.

## Prerequisites

- Python 3.10 or higher
- A [Google AI Studio](https://aistudio.google.com/apikey) API key for Gemini 2.5 Flash
- Internet access (for MCP weather/currency APIs and first-time embedding model download)

## Setup and Run (Step by Step)

### Step 1 — Go to the project folder

```bash
cd /Users/Ishan_Gaurav/Documents/Python-Play/mcp
```

### Step 2 — Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> First install may take a few minutes (downloads embedding model dependencies).

### Step 4 — Set your Gemini API key

Open `backend\config.py` and set your key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### Step 5 — Create knowledge markdown files (optional)

Download travel content from public sources into `knowledge/`:

```bash
python knowledge_scripts/create_knowledge_base.py
```

This creates 3 plain markdown files in `knowledge/`. Source titles and URLs are defined in `backend/config.py` (`KNOWLEDGE_SOURCES`).

> Skip this step if the markdown files already exist in `knowledge/`.

### Step 6 — Build the vector store (first time only)

```bash
python knowledge_scripts/build_vector_store.py
```

This reads the markdown files in `knowledge/`, creates embeddings, and saves them to `vector_store/`. The app loads this index at startup via `load_vector_store()` — run this script before launching the app.

### Step 7 — Run the app

```bash
streamlit run frontend/travel_assistant_frontend.py
```

The app opens in your browser (usually `http://localhost:8501`).

### Quick Run (after first setup)

If you already completed setup once, use:

```bash
source .venv/bin/activate
streamlit run frontend/travel_assistant_frontend.py
```



## Example Questions

- What are the must-visit attractions in Singapore?
- How can a tourist travel around Singapore?
- What is the weather forecast for the next 3 days?
- Convert INR 50,000 to SGD.
- Plan a three-day trip to Singapore and adjust activities based on the weather forecast.
- I have a budget of INR 60,000. Convert it to SGD and suggest a three-day itinerary.

## Project Structure

```
├── backend/
│   ├── travel_assistant_backend.py  # LangGraph agent (RAG + MCP)
│   ├── config.py                    # Configuration
│   ├── prompts.py                   # System prompt
│   └── rag.py                       # Retrieval pipeline
├── frontend/
│   └── travel_assistant_frontend.py # Streamlit UI
├── knowledge/                       # Travel guide markdown files
├── knowledge_scripts/
│   ├── create_knowledge_base.py     # Download & create knowledge MD files
│   └── build_vector_store.py        # Build Chroma embeddings
├── mcp_servers/                     # Weather and currency MCP servers
└── vector_store/                    # Chroma persistence (auto-generated)
```

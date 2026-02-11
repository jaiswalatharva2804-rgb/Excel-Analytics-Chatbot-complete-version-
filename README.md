# Excel Analytics Chatbot

An intelligent chatbot for analyzing Excel/CSV data using natural language queries. **Runs 100% locally** using Ollama LLMs and local embeddings - no external API calls.

## Features

- **🔒 Fully Local**: Uses Ollama (local LLM) and sentence-transformers (local embeddings)
- **📊 Any Excel/CSV File**: Load and analyze any data file
- **🧠 Smart Routing**: Automatically routes questions to the best analysis method
- **📝 Column Explanation**: Properly explains all columns and data structure
- **📈 Trend Analysis**: Analyze patterns over time
- **🔍 Hybrid Analysis**: Combines numerical + text analysis for comprehensive insights
- **🌐 API Ready**: Clean API layer for web/app integration

## Query Types

| Query Type | Handler | Example Questions |
|------------|---------|-------------------|
| **Schema** | SchemaHandler | "What columns are available?", "Explain all columns" |
| **SQL** | SQLHandler | "How many records?", "Average rating?", "Top 10 by score" |
| **Cluster** | ClusterHandler | "Most common complaints?", "Main issues?" |
| **RAG** | RAGHandler | "Why are customers unhappy?", "Explain the issues" |
| **Trend** | TrendAnalyzer | "Show the trend over time", "Monthly patterns" |
| **Overview** | HybridHandler | "Give me an overview", "Summarize the data" |
| **Hybrid** | HybridHandler | "Analyze discount trends", "Insights on ratings" |

## Project Structure

```
excel_analytics_chatbot/
├── core/                    # Core modules
│   ├── config.py           # Configuration (local models)
│   ├── llm.py              # Ollama LLM interface
│   ├── embeddings.py       # Local sentence embeddings
│   └── database.py         # DuckDB operations
├── handlers/               # Question handlers
│   ├── sql_handler.py      # SQL queries
│   ├── cluster_handler.py  # Text clustering
│   ├── rag_handler.py      # Semantic search
│   ├── schema_handler.py   # Column explanations ⭐
│   ├── hybrid_handler.py   # Combined analysis ⭐
│   ├── trend_analyzer.py   # Time-based trends
│   └── data_profiler.py    # Data profiling
├── api/                    # API layer ⭐
│   ├── __init__.py
│   └── chatbot_api.py      # JSON API for web/app
├── utils/
│   └── vector_store.py     # FAISS vector store
├── app.py                  # Main application
├── question_router.py      # Smart routing
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
```

## Prerequisites

1. **Ollama** running locally:
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3:8b
   ollama serve
   ```

2. **Dependencies** (auto-installed):
   - sentence-transformers (local embeddings)
   - duckdb (database)
   - faiss-cpu (vector search)
   - scikit-learn (clustering)

## Usage

### Interactive Mode

```bash
python app.py
```

**Commands:**
- `load <path>` - Load a CSV or Excel file
- `help` - Show available commands
- `schema` - Quick column overview
- `columns` - Detailed column explanations
- `tables` - List loaded tables
- `quit` - Exit

### Example Questions

```
🧑 You: What columns are available?
🤖 Bot: [Lists all columns with types and descriptions]

🧑 You: Explain all the columns
🤖 Bot: [Detailed explanation of each column]

🧑 You: How many records are there?
🤖 Bot: [SQL-based count with insights]

🧑 You: Give me an overview of the data
🤖 Bot: [Comprehensive dataset overview]

🧑 You: What are the most common complaints?
🤖 Bot: [Clustering analysis of text patterns]

🧑 You: Give me insights on the discount trends
🤖 Bot: [Hybrid analysis combining numerical and text data]
```

### Programmatic Usage

```python
from app import ExcelAnalyticsChatbot

# Initialize
chatbot = ExcelAnalyticsChatbot()

# Load any CSV or Excel file
chatbot.load_data("path/to/your/data.csv")

# Ask questions
print(chatbot.ask("What columns are available?"))      # Schema
print(chatbot.ask("How many records are there?"))       # SQL
print(chatbot.ask("What are the most common issues?"))  # Cluster
print(chatbot.ask("Why are customers unhappy?"))        # RAG
print(chatbot.ask("Show the trend over time"))          # Trend
print(chatbot.ask("Give me an overview"))               # Overview

# Close
chatbot.close()
```

### API Usage (for Web/App Integration)

```python
from api import ChatbotAPI, create_api

# Quick setup
api = create_api("path/to/data.csv")

# Or manual setup
api = ChatbotAPI()
result = api.load_file("path/to/data.csv")

# Ask questions (returns JSON-like response)
response = api.ask("What columns are available?")
print(response.data["answer"])

# Get schema
schema = api.get_schema(detailed=True)

# Get overview
overview = api.get_overview()

# Execute SQL directly
result = api.execute_sql("SELECT * FROM data LIMIT 10")

api.close()
```

## Configuration

Environment variables:
- `OLLAMA_URL`: Ollama API URL (default: `http://localhost:11434/api/chat`)
- `LLM_MODEL`: LLM model (default: `llama3:8b`)
- `EMBEDDING_MODEL`: Embedding model (default: `all-MiniLM-L6-v2`)
- `DB_PATH`: Database path (default: `data/analytics.duckdb`)

## How It Works

1. **Load Data**: CSV/Excel → DuckDB table
2. **Route Question**: Smart router analyzes question type
3. **Select Handler**: Routes to appropriate handler (SQL, Cluster, RAG, Schema, Trend, Hybrid)
4. **Process**: Handler retrieves/analyzes data
5. **Generate Response**: LLM formats results into natural language

## Local Model Requirements

- **LLM**: Ollama with llama3:8b (or any compatible model)
  - Alternatives: `mistral:7b`, `llama2:7b`, `codellama:7b`
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2`
  - Alternatives: `all-mpnet-base-v2` (higher quality)

## Troubleshooting

**"Cannot connect to Ollama"**
```bash
# Make sure Ollama is running
ollama serve
```

**"Model not found"**
```bash
# Pull the model
ollama pull llama3:8b
```

**Slow responses**
- Use a smaller model: `mistral:7b`
- Reduce `RAG_TOP_K` in config.py

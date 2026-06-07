<p align="center">
  <img src="https://raw.githubusercontent.com/dungnotnull/nontech-data-analyst-agent/main/assets/logo.svg" alt="NonTech Data Analyst Agent" width="120" />
</p>

<h1 align="center">NonTech Data Analyst Agent</h1>

<p align="center">
  <strong>Your AI business analyst — no SQL, no Python, no headaches.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#api-reference">API</a> ·
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/fastapi-0.110+-green.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/react-18+-61DAFB.svg" alt="React" />
  <img src="https://img.shields.io/badge/license-MIT-brightgreen.svg" alt="License" />
  <img src="https://img.shields.io/badge/languages-20+%20languages%20%7C%20bilingual%20core-orange.svg" alt="Languages" />
</p>

---

## What Is This?

**NonTech Data Analyst Agent** turns messy Excel and CSV files into clear, actionable business insights — using nothing but plain natural language. No SQL. No Python. No PivotTables. No headaches.

Upload your revenue sheet. Ask *"Which products sold best last month?"* or *"Is my revenue trending up or down?"* Get back a beautiful chart, a written explanation, and a strategic recommendation. That's it.

It's built for **small business owners**, **café managers**, **retail shop operators**, **sales teams**, and anyone who sits on mountains of data but doesn't have a data analyst on payroll. The core is bilingual (Vietnamese + English) with an architecture designed to extend to any language.

---

## Features

### 📁 Smart File Ingestion
Drag-and-drop Excel (.xlsx, .xls), CSV, TSV, and ODS files up to 50MB. The system auto-detects encoding, handles merged cells, parses international date formats (including `dd/mm/yyyy` and `month year`), recognizes currency columns (₫, $, €, VND, USD), and normalizes everything into clean pandas DataFrames. Chunked loading for large files and sheet preview for multi-sheet workbooks.

### 🔍 Automatic Schema Discovery
You don't tell the system what your columns mean — it figures it out. Column types (numeric, categorical, datetime, currency, percentage, boolean), suggested roles (revenue metric, product dimension, date field, region dimension), missing value statistics, unique value counts, and date ranges are all detected automatically.

### 🧠 Natural Language Understanding
Ask questions in plain language. The intent parser extracts the analysis type, metric, dimensions, time filters, sort order, and chart preferences from your question. Backed by a 50+ pattern rule engine with LLM fallback via Claude, GPT-4o, or Gemini. Detects 9 distinct analysis types: ranking, trend, comparison, distribution, anomaly, profitability, segmentation, forecast, and summary.

### ⚡ Secure Code Execution Sandbox
Every computation runs through a Python sandbox with AST-level code validation, multiprocess isolation, and a 30-second timeout. Only whitelisted libraries (pandas, numpy, scikit-learn, plotly) can be imported. No filesystem access outside the session directory. No network calls. No escape vectors.

### 📊 Beautiful Auto-Generated Charts
Plotly-powered interactive visualizations auto-selected based on your question:

| Question Type | Chart |
|---|---|
| "Top/best/worst" | Horizontal bar chart |
| "Trend over time" | Line chart with area fill |
| "Compare A vs B" | Grouped bar chart |
| "Distribution/spread" | Histogram + box plot |
| "Anything unusual?" | Anomaly indicator gauge |
| "Profit/loss" | Dual-axis revenue-profit chart |
| "Segments/groups" | Donut pie chart |
| "Forecast/predict" | Line chart with confidence bands |

All charts use colorblind-safe palettes, proper labels, and export to PNG or interactive HTML.

### 📝 Plain-Language Business Narratives
Charts alone don't drive decisions — stories do. Every analysis produces a structured narrative: the key finding, comparison to previous periods, and actionable next steps. Numbers are always accompanied by interpretation:

> *"📊 Revenue Ranking Results: Top 3 — Iced Milk Coffee ($10,250), Bubble Tea ($10,850), Bánh Mì ($7,520). Beverages lead with 67% of total revenue. Revenue growth of +18% vs last month."*

### 💡 Strategic Recommendations
Each analysis includes a context-aware business recommendation. Profitability analysis suggests cutting negative-margin items. Anomaly detection prompts data quality checks. Segmentation recommends VIP retention strategies. These aren't generic — they're driven by what the data actually says.

### 🔮 Time-Series Forecasting
Prophet-based forecasting with automatic holiday calendar integration. Falls back to StatsForecast (AutoARIMA/AutoETS) or simple moving average for short series. Produces confidence intervals, trend decomposition, and model evaluation metrics (MAPE, RMSE, MAE, MASE).

### 🚨 Anomaly Detection
Isolation Forest, LOF, Z-score, and IQR-based detection for cross-sectional anomalies. Rolling Z-score and IQR for time-series. Each detected anomaly comes with a plain-language explanation of *which* combination of features makes it unusual and what you should investigate.

### 👥 Customer & Product Segmentation
KMeans with auto-k selection via silhouette scores. DBSCAN for arbitrary-shaped clusters. RFM (Recency-Frequency-Monetary) analysis for customer value segmentation. Segments are auto-labeled: "VIP/Champions", "Loyal Customers", "At-Risk", "New/Casual".

### 📚 Self-Learning Knowledge Brain
Crawls arXiv and Semantic Scholar weekly for the latest research on retail analytics, time-series forecasting, anomaly detection, and NLP. Papers are embedded into ChromaDB for semantic search. When generating strategic recommendations, the agent retrieves relevant research and cites it — becoming smarter over time without any human intervention.

---

## Quick Start

### Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | React frontend |
| Docker | 24+ | Containerized deployment (optional) |

### 1. Clone & Setup

```bash
git clone https://github.com/dungnotnull/nontech-data-analyst-agent.git
cd nontech-data-analyst-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
```

### 2. Start the Backend

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger API documentation.

### 3. Start the Frontend

**React (production):**
```bash
cd src/ui/react_app
npm install
npm run dev
# → http://localhost:5173
```

**Streamlit (quick demo):**
```bash
streamlit run src/ui/streamlit_app.py
# → http://localhost:8501
```

### 4. Docker (all-in-one)

```bash
docker-compose up --build
# API:        http://localhost:8000
# Streamlit:  http://localhost:8501
```

---

## How It Works

### The End-to-End Pipeline

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Upload File  │────▶│  Schema Detector │────▶│  Clean & Normalize│
│  (.xlsx/.csv) │     │  (auto-types)    │     │  (handle missing) │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                      │
┌──────────────┐     ┌─────────────────┐              │
│   Natural     │────▶│  Intent Parser   │◀─────────────┘
│   Language    │     │  (rules + LLM)   │
│   Question    │     └────────┬────────┘
└──────────────┘              │
                     {analysis_type, metric,
                      dimensions, time_filter}
                              │
┌──────────────┐     ┌───────▼─────────┐
│   Chart       │◀────│  Code Generator  │
│   Renderer    │     │  (pandas template)│
│   (Plotly)    │     └───────┬─────────┘
└──────┬───────┘             │
       │              ┌──────▼─────────┐
       │              │  Python Sandbox │
       │              │  (AST + timeout)│
       │              └──────┬─────────┘
       │                     │ DataFrame
       ▼                     ▼
┌──────────────────────────────────────┐
│         Narrative Writer             │
│    (structured business language)    │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│  Response: Chart + Narrative + Tip   │
└──────────────────────────────────────┘
```

### Analysis Types

| Analysis | What It Does | Example Question |
|---|---|---|
| **Ranking** | Top/bottom N by any metric | "Which products sold best last month?" |
| **Trend** | How a metric changes over time | "Is revenue trending up or down?" |
| **Comparison** | Compare across dimensions | "Compare revenue across regions" |
| **Distribution** | Statistical spread of values | "How are order values distributed?" |
| **Anomaly** | Flag unusual data points | "Which costs are abnormally high?" |
| **Profitability** | Revenue vs cost analysis | "Which products are losing money?" |
| **Segmentation** | Cluster products/customers | "How many customer segments do I have?" |
| **Forecast** | Predict future values | "Forecast next month's revenue" |
| **Summary** | Overall data overview | "Give me an overview of this data" |

---

## Architecture

```
nontech-data-analyst-agent/
│
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # App entry, middleware, lifespan
│   │   ├── sandbox.py          # Secure Python execution engine
│   │   ├── rate_limiter.py     # IP-based rate limiting
│   │   ├── logging_config.py   # Structured logging (rotating files)
│   │   ├── session_cleaner.py  # Ephemeral file cleanup (24h TTL)
│   │   └── routes/
│   │       ├── upload.py       # POST /api/upload
│   │       ├── analyze.py      # POST /api/analyze
│   │       └── knowledge.py    # GET/POST /api/knowledge/*
│   │
│   ├── agent/                  # Core intelligence pipeline
│   │   ├── intent_parser.py    # NLU: rules + LLM intent extraction
│   │   ├── code_generator.py   # Intent → pandas code (9 templates)
│   │   ├── chart_renderer.py   # Plotly chart factory (10 chart types)
│   │   ├── narrative_writer.py # Structured business narratives
│   │   └── knowledge_updater.py# arXiv/Semantic Scholar crawler
│   │
│   ├── data/                   # Data processing layer
│   │   ├── file_loader.py      # Excel/CSV/ODS with encoding detection
│   │   ├── schema_detector.py  # Auto-detect columns, types, roles
│   │   └── cleaner.py          # Missing values, outliers, normalization
│   │
│   ├── models/                 # ML/Analytics models
│   │   ├── forecaster.py       # Prophet + StatsForecast + SMA
│   │   ├── anomaly_detector.py # IsolationForest + LOF + Z-score + IQR
│   │   └── segmenter.py        # KMeans + DBSCAN + RFM
│   │
│   ├── ui/                     # Frontend applications
│   │   ├── streamlit_app.py    # Quick demo interface
│   │   └── react_app/          # Production React + TypeScript + Tailwind
│   │
│   └── config/                 # Application configuration
│       ├── settings.py         # All environment variables + defaults
│       └── llm_config.py       # LLM provider registry + fallback chain
│
├── data_samples/               # Example CSV files
├── assets/                     # Logo and static assets
├── pyproject.toml              # Package metadata + build configuration
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # Orchestrated services
├── Makefile                    # Developer convenience commands
└── CLAUDE.md                   # Agent identity + behavior specification
```

---

## API Reference

### Health Check

```http
GET /health
```

```json
{"status": "ok", "version": "0.2.0", "timestamp": 1780837453.21}
```

### Upload File

```http
POST /api/upload
Content-Type: multipart/form-data

file: revenue_data.csv
```

```json
{
  "session_id": "a1b2c3d4-...",
  "file_name": "revenue_data.csv",
  "file_size_mb": 2.34,
  "sheets": ["data"],
  "schemas": {
    "data": {
      "columns": ["date", "product", "category", "region", "quantity", "unit_price", "revenue", "cost"],
      "row_count": 65,
      "column_types": {
        "date": "datetime",
        "product": "text",
        "category": "categorical",
        "region": "categorical",
        "quantity": "numeric",
        "unit_price": "numeric",
        "revenue": "numeric",
        "cost": "numeric"
      },
      "suggested_roles": {
        "date": "date",
        "revenue": "metric_revenue",
        "cost": "metric_cost",
        "product": "dimension_product",
        "region": "dimension_region"
      }
    }
  }
}
```

### Analyze Data

```http
POST /api/analyze
Content-Type: application/json

{
  "session_id": "a1b2c3d4-...",
  "question": "which products sell best?"
}
```

```json
{
  "session_id": "a1b2c3d4-...",
  "question": "which products sell best?",
  "intent": {
    "analysis_type": "ranking",
    "metric": "revenue",
    "language": "en",
    "confidence": 0.85
  },
  "result": [
    {"dimension": "Beverages", "value": 9889},
    {"dimension": "Food", "value": 4855}
  ],
  "chart_html": "<div>...</div>",
  "narrative": "📊 **Revenue Ranking:**\n\n**Top 2:**\n  • Beverages: 9,889\n  • Food: 4,855",
  "recommendation": "💡 **Tip:** Focus resources on the leading categories. Consider reducing stock or discontinuing bottom performers.",
  "error": null
}
```

### Knowledge Brain

```http
GET /api/knowledge/status
```

```json
{
  "last_update": "2025-06-01",
  "total_entries": 23,
  "total_papers_indexed": 23,
  "topics_tracked": ["time series forecasting retail", "business data analysis LLM", "anomaly detection tabular data", "customer segmentation"]
}
```

```http
POST /api/knowledge/update
```

```http
GET /api/knowledge/search?q=retail+forecasting&top_k=3
```

---

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `claude` | `claude`, `openai`, `gemini`, or `local` |
| `LLM_API_KEY` | — | Your LLM API key |
| `LLM_MODEL` | `claude-sonnet-4-20250514` | Model identifier |
| `APP_ENV` | `development` | `development`, `staging`, `production` |
| `APP_DEBUG` | `true` | Enable debug mode (API docs, verbose logging) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size |
| `SESSION_TTL_HOURS` | `24` | Auto-delete uploaded files after N hours |
| `SANDBOX_TIMEOUT_SECONDS` | `30` | Maximum code execution time |
| `SANDBOX_MAX_MEMORY_MB` | `512` | Memory limit for sandbox process |
| `KNOWLEDGE_CRAWL_ENABLED` | `false` | Enable weekly paper crawling |
| `KNOWLEDGE_CRAWL_SCHEDULE` | `0 2 * * 1` | Cron: every Monday 2AM |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Security Design

This system processes user-uploaded data and executes generated code. Security is built into the architecture, not bolted on.

**Sandbox Isolation**
- Every user computation runs in a separate `multiprocessing.Process`
- AST-level validation blocks all forbidden imports (`os`, `subprocess`, `socket`, `shutil`, `requests`, `ctypes`, `pickle`, etc.)
- Whitelisted modules only: `pandas`, `numpy`, `matplotlib`, `plotly`, `scikit-learn`, `statsmodels`, `prophet`
- 30-second timeout enforced via `Process.join()` — cross-platform compatible (Windows + Unix)

**File Isolation**
- Uploads stored in UUID-based session directories with zero cross-session access
- `SessionCleaner` deletes all files after configurable TTL (default 24 hours)
- No persistent storage of user data beyond the session lifetime

**API Security**
- Rate limiting: 10 uploads/hour, 100 analyses/hour per IP address
- Security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`
- `Server` header stripped from responses
- GZip compression for responses > 1KB
- CORS with configurable origins

**LLM API Privacy**
- Only schema metadata and aggregated statistics sent to external LLM APIs
- Maximum 20 sample rows transmitted — never raw full datasets
- User PII never leaves the sandbox

**Error Handling**
- All exceptions caught at middleware level — no stack traces leak to clients
- Error messages returned in plain language, not technical jargon
- Separate rotating error log file for production monitoring

---

## Sample Data

The `data_samples/` directory contains real-world business data ready for exploration:

**revenue_data.csv** — 6 months of café sales (65 rows)
- Columns: date, product, category, region, quantity, unit price, revenue, cost
- 6 products across 3 regions with realistic seasonality patterns

**inventory_data.csv** — 15 products with stock levels
- Columns: item, opening stock, purchases, sales, closing stock, cost price, selling price
- Ready for ABC/Pareto analysis and inventory turnover calculations

**expenses_data.csv** — 40 operational expense entries
- Columns: date, expense type, description, amount, responsible person, category
- Includes rent, salaries, marketing, maintenance, utilities
- Contains deliberate outliers for anomaly detection testing

---

## Contributing

Contributions are welcome. Areas where help is especially valuable:

- 🌏 **Languages**: Adding support for new languages to the intent parser and narrative writer
- 🗺️ **GeoJSON maps**: High-quality regional map files for choropleth visualizations
- 📊 **Analysis templates**: New business analysis types and code generation patterns
- 🧪 **Test suite**: Real-world Excel file edge cases and integration tests
- 🔌 **LLM providers**: Adding support for local models (Ollama, vLLM, llama.cpp)
- 📱 **Mobile UX**: Improving the React frontend for tablet and mobile use

```bash
# Development setup
git clone https://github.com/dungnotnull/nontech-data-analyst-agent.git
cd nontech-data-analyst-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make lint    # Ruff check
make test    # Pytest
make dev     # Start development server
```

---

## License

MIT © 2025 NonTech Data Analyst Agent Contributors

---

<p align="center">
  <em>"Your AI business analyst. Just ask in plain language — we'll handle the rest."</em>
</p>

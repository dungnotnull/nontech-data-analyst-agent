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
  <img src="https://img.shields.io/badge/languages-Vietnamese%20%7C%20English-orange.svg" alt="Languages" />
</p>

---

## What Is This?

**NonTech Data Analyst Agent** turns messy Excel and CSV files into clear, actionable business insights — using nothing but plain Vietnamese or English. No SQL. No Python. No PivotTables. No headaches.

Upload your revenue sheet. Ask *"Mặt hàng nào bán chạy nhất tháng vừa rồi?"* Get back a beautiful chart, a written explanation, and a strategic recommendation. That's it.

It's built for **small business owners**, **café managers**, **retail shop operators**, **sales teams**, and anyone who sits on mountains of data but doesn't have a data analyst on payroll.

---

## Features

### 📁 Smart File Ingestion
Drag-and-drop Excel (.xlsx, .xls), CSV, or TSV files up to 50MB. The system auto-detects encoding, handles merged cells, parses Vietnamese dates (`tháng 6 năm 2025`), recognizes VND/USD currency columns, and normalizes everything into clean pandas DataFrames.

### 🔍 Automatic Schema Discovery
You don't tell the system what your columns mean — it figures it out. Column types (numeric, categorical, datetime, currency, percentage), suggested roles (revenue metric, product dimension, date field), missing value statistics, and date ranges are all detected automatically.

### 🧠 Bilingual Natural Language Understanding
Ask questions in Vietnamese or English. Type with or without diacritics — both `"sản phẩm nào bán chạy?"` and `"san pham nao ban chay?"` work. The intent parser extracts the analysis type, metric, dimensions, time filters, and chart preferences from your question. Backed by a 50+ pattern rule engine with LLM fallback via Claude/GPT-4o/Gemini.

### ⚡ Secure Code Execution Sandbox
Every computation runs through a Python sandbox with AST-level code validation, multiprocess isolation, and a 30-second timeout. Only whitelisted libraries (pandas, numpy, scikit-learn) can be imported. No filesystem access outside the session directory. No network calls. No escape vectors.

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

### 📝 Plain-Language Business Narratives
Charts alone don't drive decisions — stories do. Every analysis produces a structured narrative in your language: the key finding, comparison to previous periods, and actionable next steps. Numbers are always accompanied by interpretation:

> *"📊 Kết quả xếp hạng theo doanh thu: Top 3 cao nhất — Cà Phê Sữa Đá (10,250,000), Trà Sữa Trân Châu (10,850,000), Bánh Mì Thịt (7,520,000). Đồ uống dẫn đầu với 67% tổng doanh thu."*

### 💡 Strategic Recommendations
Each analysis includes a context-aware business recommendation. Profitability analysis suggests cutting negative-margin items. Anomaly detection prompts data quality checks. Segmentation recommends VIP retention strategies. These aren't generic — they're driven by what the data actually says.

### 🔮 Time-Series Forecasting
Prophet-based forecasting with automatic Vietnamese holiday calendar integration (Tết Nguyên Đán, Reunification Day, National Day). Falls back to StatsForecast (AutoARIMA/AutoETS) or simple moving average for short series. Produces confidence intervals and trend decomposition.

### 🚨 Anomaly Detection
Isolation Forest, LOF, Z-score, and IQR-based detection for cross-sectional anomalies. Rolling Z-score and IQR for time-series. Each detected anomaly comes with a plain-language explanation of *which* combination of features makes it unusual.

### 👥 Customer & Product Segmentation
KMeans with auto-k selection via silhouette scores. DBSCAN for arbitrary-shaped clusters. RFM (Recency-Frequency-Monetary) analysis for customer value segmentation. Segments are auto-labeled: "VIP/Champions", "Có nguy cơ rời bỏ", "Mới/Cần chăm sóc".

### 📚 Self-Learning Knowledge Brain
Crawls arXiv and Semantic Scholar weekly for the latest research on retail analytics, time-series forecasting, anomaly detection, and Vietnamese NLP. Papers are embedded into ChromaDB for semantic search. When generating strategic recommendations, the agent retrieves relevant research and cites it — becoming smarter over time without any human intervention.

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
# API:     http://localhost:8000
# Streamlit: http://localhost:8501
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
│  Vietnamese   │────▶│  Intent Parser   │◀─────────────┘
│  question     │     │  (rules + LLM)   │
└──────────────┘     └────────┬────────┘
                              │
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
│         Narrative Writer              │
│    (structured bilingual output)      │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│  Response: Chart + Narrative + Tip   │
└──────────────────────────────────────┘
```

### Analysis Types

| Analysis | What It Does | Example Question |
|---|---|---|
| **Ranking** | Top/bottom N by any metric | "Sản phẩm nào bán chạy nhất?" |
| **Trend** | How a metric changes over time | "Doanh thu có xu hướng tăng hay giảm?" |
| **Comparison** | Compare across dimensions | "So sánh doanh thu các khu vực" |
| **Distribution** | Statistical spread of values | "Phân bố giá trị đơn hàng thế nào?" |
| **Anomaly** | Flag unusual data points | "Chi phí nào tăng bất thường?" |
| **Profitability** | Revenue vs cost analysis | "Mặt hàng nào đang bị lỗ?" |
| **Segmentation** | Cluster products/customers | "Khách hàng chia thành mấy nhóm?" |
| **Forecast** | Predict future values | "Dự báo doanh thu tháng tới" |
| **Summary** | Overall data overview | "Cho tôi tổng quan về dữ liệu" |

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
│   │   ├── narrative_writer.py # Bilingual business narratives
│   │   └── knowledge_updater.py# arXiv/Semantic Scholar crawler
│   │
│   ├── data/                   # Data processing layer
│   │   ├── file_loader.py      # Excel/CSV with encoding detection
│   │   ├── schema_detector.py  # Auto-detect columns, types, roles
│   │   └── cleaner.py          # Missing values, outliers, normalization
│   │
│   ├── models/                 # ML/Analytics models
│   │   ├── forecaster.py       # Prophet + StatsForecast + SMA
│   │   ├── anomaly_detector.py # IsolationForest + LOF + Z-score
│   │   └── segmenter.py        # KMeans + DBSCAN + RFM
│   │
│   ├── ui/                     # Frontend applications
│   │   ├── streamlit_app.py    # Quick demo interface
│   │   └── react_app/          # Production React + TypeScript
│   │       ├── src/
│   │       │   ├── components/ # FileUpload, ChatPanel, SchemaViewer
│   │       │   ├── hooks/      # Zustand state management
│   │       │   ├── services/   # API client
│   │       │   └── types/      # TypeScript definitions
│   │       ├── package.json
│   │       └── vite.config.ts
│   │
│   └── config/                 # Application configuration
│       ├── settings.py         # All env vars + defaults
│       └── llm_config.py       # LLM provider registry + fallback
│
├── data_samples/               # Example CSV files
│   ├── revenue_data.csv        # 6 months of café sales data
│   ├── inventory_data.csv      # 15 products with stock levels
│   └── expenses_data.csv       # Operational expenses
│
├── SECOND-KNOWLEDGE-BRAIN.md   # Curated research knowledge base
├── PROJECT-detail.md           # Full technical specification
├── pyproject.toml              # Package metadata + build config
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # Orchestrated services
├── Makefile                    # Developer convenience commands
└── CLAUDE.md                   # Agent identity + behavior rules
```

---

## API Reference

### Health Check

```http
GET /health
```

```json
{"status": "ok", "version": "0.1.0", "timestamp": 1780837453.21}
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
      "columns": ["ngay", "san_pham", "danh_muc", "khu_vuc", "so_luong", "don_gia", "doanh_thu", "chi_phi"],
      "row_count": 65,
      "column_types": {
        "ngay": "datetime",
        "san_pham": "text",
        "danh_muc": "categorical",
        "khu_vuc": "categorical",
        "so_luong": "numeric",
        "don_gia": "numeric",
        "doanh_thu": "numeric",
        "chi_phi": "numeric"
      },
      "suggested_roles": {
        "ngay": "date",
        "doanh_thu": "metric_revenue",
        "chi_phi": "metric_cost"
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
  "question": "san pham nao ban chay nhat?"
}
```

```json
{
  "session_id": "a1b2c3d4-...",
  "question": "san pham nao ban chay nhat?",
  "intent": {
    "analysis_type": "ranking",
    "metric": "auto",
    "language": "vi",
    "confidence": 0.6
  },
  "result": [
    {"dimension": "Đồ uống", "value": 9889},
    {"dimension": "Đồ ăn", "value": 4855}
  ],
  "chart_html": "<div>...</div>",
  "narrative": "📊 **Kết quả xếp hạng theo giá trị:**\n\n**Top 2 cao nhất:**\n  • Đồ uống: 9,889\n  • Đồ ăn: 4,855",
  "recommendation": "💡 **Gợi ý:** Tập trung nguồn lực vào các mặt hàng dẫn đầu.",
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
  "topics_tracked": ["time series forecasting retail", "business data analysis LLM", ...]
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
| `LLM_MODEL` | `claude-sonnet-4-20250514` | Model to use |
| `APP_ENV` | `development` | `development`, `staging`, `production` |
| `APP_DEBUG` | `true` | Enable debug mode (docs, verbose logging) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size |
| `SESSION_TTL_HOURS` | `24` | Auto-delete uploaded files after N hours |
| `SANDBOX_TIMEOUT_SECONDS` | `30` | Maximum code execution time |
| `SANDBOX_MAX_MEMORY_MB` | `512` | Memory limit for sandbox process |
| `KNOWLEDGE_CRAWL_ENABLED` | `false` | Enable weekly paper crawling |
| `KNOWLEDGE_CRAWL_SCHEDULE` | `0 2 * * 1` | Cron: every Monday 2AM |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Security Design

This system processes user-uploaded data and executes generated code. Security is not an afterthought — it's baked into the architecture:

**Sandbox Isolation**
- Every user computation runs in a separate `multiprocessing.Process`
- AST-level validation blocks all forbidden imports (os, subprocess, socket, etc.)
- Whitelisted modules only: pandas, numpy, matplotlib, plotly, scikit-learn, statsmodels, prophet
- 30-second timeout enforced via `Process.join()` — Windows + Unix compatible

**File Isolation**
- Uploads stored in UUID-based session directories with no cross-session access
- SessionCleaner deletes all files after configurable TTL (default 24h)
- No persistent storage of user data beyond the session lifetime

**API Security**
- Rate limiting: 10 uploads/hour, 100 analyses/hour per IP address
- Security headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`
- GZip compression for responses > 1KB
- CORS restricted to configurable origins

**LLM API Privacy**
- Only schema metadata + aggregated statistics sent to external LLM APIs
- Maximum 20 sample rows sent — never raw full datasets
- PII removal: column values inspected for email/phone/address patterns before transmission

**Error Handling**
- All exceptions caught at middleware level — no stack traces leak to clients
- Error messages returned in Vietnamese/English plain language
- Separate error log for production monitoring

---

## Sample Data

The `data_samples/` directory contains real-world-style Vietnamese business data:

**revenue_data.csv** — 6 months of café sales (65 rows)
- Columns: date, product, category, region, quantity, unit price, revenue, cost
- 6 products across 3 regions (Hồ Chí Minh, Hà Nội, Đà Nẵng)
- Realistic seasonality patterns

**inventory_data.csv** — 15 products with stock levels
- Columns: item, opening stock, purchases, sales, closing stock, cost price, selling price
- Ready for ABC/Pareto analysis and inventory turnover calculations

**expenses_data.csv** — 40 operational expense entries
- Columns: date, expense type, description, amount, responsible person, category
- Includes rent, salaries, marketing, maintenance, utilities
- Contains intentionally high electricity bills for anomaly detection testing

---

## Contributing

Contributions are welcome. Areas where help is especially valuable:

- 🌏 **Translations**: Adding more languages to the narrative writer
- 🗺️ **Vietnam GeoJSON**: High-quality province-level map for choropleth
- 📊 **Analysis templates**: New business analysis types
- 🧪 **Test suite**: Real-world Excel file edge cases
- 🔌 **LLM providers**: Adding support for local models (Ollama, vLLM)

```bash
# Dev setup
git clone https://github.com/dungnotnull/nontech-data-analyst-agent.git
cd nontech-data-analyst-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make lint    # Ruff check
make test    # Pytest
make dev     # Start dev server
```

---

## License

MIT © 2025 NonTech Data Analyst Agent Contributors

---

<p align="center">
  <em>"Tôi là trợ lý phân tích số liệu của bạn. Bạn chỉ cần hỏi bằng tiếng Việt tự nhiên — tôi sẽ lo phần còn lại."</em>
</p>

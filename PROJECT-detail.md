# PROJECT-detail.md — NonTech Data Analyst Agent
## Full Technical Specification

---

## 1. Problem Statement

Small business owners and non-technical sales/operations staff in Vietnam and Southeast Asia sit on goldmines of data — Excel sheets tracking revenue, expenses, inventory, and customers — yet cannot extract value from them without hiring expensive analysts or learning programming. This project removes that barrier entirely.

**Pain points addressed:**
- Cannot identify which products/regions are profitable vs. loss-making
- Unable to spot trends or seasonality without pivot tables knowledge
- No access to forecasting for inventory planning
- Overwhelmed by raw numbers with no business narrative

---

## 2. Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Non-technical usability | User can get insight without any tutorial | ≥ 90% task completion by first-time users |
| Accuracy | Numeric outputs match manual calculation | 100% (all via code execution) |
| Response speed | Time from question to chart+insight | < 15 seconds for files < 10MB |
| Self-improvement | Knowledge brain update frequency | Weekly auto-crawl |
| Multilingual | Vietnamese + English support | Both from day 1 |

---

## 3. End-to-End User Flow

```
[User] Upload Excel/CSV
         ↓
[System] Auto-detect schema (columns, data types, date formats, currency)
         ↓
[User] Type or speak a natural language question
       e.g., "Tháng vừa rồi mặt hàng nào bán chạy nhất và vùng nào đang bị lỗ?"
         ↓
[Intent Parser] Extract: metric=revenue/profit, dimension=product+region,
                time_filter=last_month, analysis_type=ranking+anomaly
         ↓
[Code Generator] Auto-generate pandas code → execute in sandbox
         ↓
[Chart Renderer] Produce bar chart (top products) + heatmap (region P&L)
         ↓
[Narrative Writer] Generate plain-language business insight:
       "Mặt hàng bán chạy nhất là Cà Phê Sữa Đá (2,340 ly, +18% vs tháng trước).
        Vùng Tây Nguyên đang lỗ 12.4 triệu đồng, chủ yếu do chi phí vận chuyển tăng."
         ↓
[Knowledge Brain] Check for relevant research to enhance recommendation
         ↓
[Output] Chart + Table + Business Narrative + Strategic Tip
```

---

## 4. Architecture

### 4.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React / Streamlit)          │
│  File Upload | Chat Interface | Chart Display | History  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                        │
│  /upload  /analyze  /forecast  /segment  /knowledge      │
└──┬──────────────┬──────────────┬──────────────┬─────────┘
   │              │              │              │
┌──▼──────┐ ┌────▼──────┐ ┌────▼──────┐ ┌────▼──────────┐
│ Intent  │ │  Python   │ │   ML/DL   │ │   Knowledge   │
│ Parser  │ │ Sandbox   │ │  Models   │ │   Updater     │
│ (LLM)   │ │(pandas +  │ │(HuggingF.)│ │(Crawl+Store)  │
└──┬──────┘ │ exec env) │ └────┬──────┘ └────┬──────────┘
   │        └────┬──────┘      │              │
   │             │             │              │
┌──▼─────────────▼─────────────▼──────────────▼──────────┐
│                   Data & Storage Layer                   │
│  Session Files (temp) | Vector DB (knowledge) | SQLite  │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Core Components

#### A. Intent Parser
- **Primary**: External LLM API (Claude Sonnet / GPT-4o) via user-provided key
- **Fallback**: Fine-tuned classification model on HuggingFace
  - Recommended: `microsoft/phi-3-mini-4k-instruct` (lightweight, fast, good Vietnamese)
  - Alternative: `vinai/phobert-base-v2` for Vietnamese-specific NLU tasks
- **Extracts**: `{metric, dimensions, time_filter, analysis_type, chart_preference}`
- **Output format**: Structured JSON passed to Code Generator

#### B. Python Sandbox (Code Execution Engine)
- **Technology**: RestrictedPython + subprocess isolation
- **Libraries available inside sandbox**: pandas, numpy, matplotlib, plotly, scipy, statsmodels
- **Security**: No file system access outside session temp dir, no network calls, timeout 30s
- **Pattern**: Agent generates pandas code → validates syntax → executes → captures output/errors
- **Error recovery**: On exception, LLM rewrites the code with the error message as context (max 3 retries)

#### C. Data Schema Detector
- Auto-detect column types: numeric, categorical, datetime, currency, percentage
- Handle Vietnamese date formats: `dd/mm/yyyy`, `tháng X năm Y`
- Handle currency: VND (₫), USD ($), mixed formats
- Suggest column mapping when ambiguous (e.g., multiple "revenue" columns)
- **Model**: Rule-based + `dateparser` library + pandas `.infer_objects()`

#### D. Chart Renderer
- **Library**: Plotly (interactive, embeddable in React)
- **Chart types auto-selected** based on analysis type:
  - Ranking → Horizontal bar chart
  - Trend over time → Line chart with annotations
  - Comparison → Grouped bar / Radar chart
  - Distribution → Histogram + Box plot
  - Geographic → Choropleth (Vietnam provinces map via GeoJSON)
  - Correlation → Heatmap
- **Export**: PNG, SVG, interactive HTML

#### E. Narrative Writer
- Uses LLM to convert {data_summary + chart_insights} → business narrative in Vietnamese/English
- Includes: Key finding, comparison to previous period, actionable recommendation
- Template-guided to ensure consistency and prevent hallucination
- Cites `SECOND-KNOWLEDGE-BRAIN.md` when strategic recommendations are made

#### F. Knowledge Brain Updater
- **Crawler**: Fetches from arXiv, Semantic Scholar, Google Scholar, ACM Digital Library
- **Topics to track**: time-series forecasting, retail analytics, demand forecasting, customer segmentation, anomaly detection in business data, NL2SQL, NL2Code
- **Storage**: ChromaDB (vector embeddings) for semantic search + Markdown summary in `SECOND-KNOWLEDGE-BRAIN.md`
- **Schedule**: Weekly auto-run via cron/APScheduler
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace, free, fast)

---

## 5. ML/DL Models

All models prioritize pre-trained options from HuggingFace or well-established libraries. No training from scratch.

| Use Case | Model/Library | Source | Justification |
|----------|--------------|--------|---------------|
| Natural language intent parsing | `claude-sonnet-4` / `gpt-4o` | User API key | Best accuracy for complex Vietnamese queries |
| Vietnamese NLU fallback | `vinai/phobert-base-v2` | HuggingFace | Best pre-trained Vietnamese BERT |
| Lightweight LLM fallback | `microsoft/phi-3-mini-4k-instruct` | HuggingFace | Runs on CPU, good for basic intents |
| Time-series forecasting | `prophet` (Meta) | PyPI | Industry standard, handles seasonality, no training needed |
| Advanced forecasting | `statsforecast` (Nixtla) | PyPI | ARIMA/ETS/CES, fast, no GPU needed |
| Anomaly detection | `IsolationForest` | scikit-learn | Unsupervised, works on small datasets |
| Customer segmentation | `KMeans` + `DBSCAN` | scikit-learn | Standard, interpretable clusters |
| Product recommendation (future) | `LightFM` | PyPI | Hybrid collaborative filtering |
| Text embeddings (knowledge base) | `all-MiniLM-L6-v2` | HuggingFace | Lightweight semantic search |
| NL-to-Pandas code generation | LLM + custom prompt template | Via API | More reliable than specialized models |

**Design principle**: Avoid fine-tuning or training custom models unless no pre-trained alternative exists. If fine-tuning is needed, use LoRA/PEFT on the smallest viable model.

---

## 6. Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI + uvicorn
- **Data Processing**: pandas, numpy, scipy, openpyxl, xlrd
- **ML/Analytics**: scikit-learn, prophet, statsforecast, lightfm
- **Visualization**: plotly, matplotlib, seaborn
- **LLM Integration**: anthropic SDK, openai SDK, litellm (unified interface)
- **Sandbox**: RestrictedPython, resource limits via Docker
- **Vector DB**: ChromaDB (local, no server needed)
- **Task Queue**: APScheduler (lightweight) or Celery + Redis (production)
- **Database**: SQLite (dev) → PostgreSQL (production)

### Frontend
- **Quick Demo**: Streamlit (for rapid prototyping and non-tech demos)
- **Production**: React + TypeScript + Tailwind CSS
- **Charts**: Recharts (React) + Plotly.js (for complex charts)
- **File Upload**: react-dropzone
- **Chat UI**: Custom component inspired by ChatGPT interface
- **State**: Zustand

### Infrastructure
- **Containerization**: Docker + docker-compose
- **Deployment**: Railway / Render (free tier for MVP), VPS (production)
- **File Storage**: Local (dev), S3-compatible (production)
- **Auth**: Simple API key + session token (MVP), Auth0/Supabase (later)

---

## 7. Security & Privacy

- All uploaded files stored in ephemeral session directories (auto-deleted after 24h)
- Python sandbox has NO network access, NO file system access outside session dir
- No user data sent to external APIs beyond schema + statistics (never raw rows > 20)
- API keys stored in `.env`, never logged
- Rate limiting: 10 file uploads/hour, 100 analysis requests/hour per session
- File size limit: 50MB per upload
- GDPR/data minimization: no persistent storage of user data beyond session

---

## 8. Sample Questions the System Must Handle

```
"Tháng này tôi bán được bao nhiêu tiền?"
"Sản phẩm nào bán chạy nhất 3 tháng qua?"
"So sánh doanh thu tháng 5 và tháng 6"
"Vùng nào đang lỗ?"
"Dự báo doanh thu tháng tới"
"Khách hàng của tôi phân thành mấy nhóm?"
"Chi phí nào tăng bất thường?"
"Tỷ lệ lợi nhuận theo từng danh mục hàng?"
"Mặt hàng nào tồn kho lâu nhất?"
"Nhân viên bán hàng nào hiệu quả nhất?"
```

---

## 9. Limitations & Mitigations

| Limitation | Mitigation |
|-----------|------------|
| Files with inconsistent column naming | Schema detector + user confirmation step |
| Merged cells in Excel | Auto-unmerge + forward-fill on load |
| Mixed languages in data | Unicode-aware pandas + language detection |
| Very large files (>50MB) | Chunked processing + sampling for preview |
| Ambiguous questions | Clarification prompts with examples |
| No internet in sandbox | All computation is local; LLM call is outside sandbox |

---

## 10. Future Roadmap

- **v2.0**: Voice input (Whisper ASR), voice output (TTS in Vietnamese)
- **v2.1**: Multi-file join (link sales + inventory + customer sheets)
- **v2.2**: Automated weekly/monthly business report generation (PDF)
- **v3.0**: WhatsApp/Zalo bot integration for mobile-first users
- **v3.1**: Benchmarking against industry averages (retail, F&B, etc.)
- **v4.0**: Collaborative workspace (multiple users, same dataset)

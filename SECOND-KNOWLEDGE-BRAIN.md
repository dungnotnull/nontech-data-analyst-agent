# SECOND-KNOWLEDGE-BRAIN.md
## Agent's Self-Updating Core Knowledge Base
### NonTech Data Analyst Agent

> **Purpose**: This file stores curated, business-relevant knowledge extracted from research papers, technical documentation, and industry reports. The agent reads this file before generating strategic recommendations, making it smarter and more accurate over time.
>
> **Auto-Update**: The `knowledge_updater.py` module crawls arXiv, Semantic Scholar, and documentation sites weekly and appends new entries here. Older entries are summarized/compressed quarterly.
>
> **Last Full Crawl**: 2025-06-01 (manual seed — automated crawls begin after Phase 6 deployment)
> **Total Entries**: 28 (seed knowledge)
> **Topics Tracked**: Time-Series Forecasting | Retail Analytics | Anomaly Detection | Customer Segmentation | NL2Code | Business Intelligence | Vietnamese NLP

---

## INDEX
1. [Time-Series Forecasting](#1-time-series-forecasting)
2. [Retail & Business Analytics](#2-retail--business-analytics)
3. [Anomaly Detection in Business Data](#3-anomaly-detection-in-business-data)
4. [Customer & Product Segmentation](#4-customer--product-segmentation)
5. [NL2Code & Code Generation](#5-nl2code--code-generation)
6. [Vietnamese NLP](#6-vietnamese-nlp)
7. [Business Intelligence & Data Storytelling](#7-business-intelligence--data-storytelling)
8. [LLM for Data Analysis](#8-llm-for-data-analysis)

---

## 1. Time-Series Forecasting

### [KB-001] Prophet: Forecasting at Scale (Meta, 2017)
- **Source**: Taylor & Letham (2018), "Forecasting at Scale," *The American Statistician*
- **Link**: https://peerj.com/preprints/3190/
- **Key Insights**:
  - Prophet handles missing data, outliers, and multiple seasonalities (weekly, yearly) without manual configuration — ideal for small business revenue data with irregular patterns (holidays, Tet in Vietnam)
  - Additive model: trend + seasonality + holidays. Users can add custom holiday lists (Vietnamese national holidays + regional events)
  - Best for: weekly/monthly business revenue, sales volume with clear seasonality
  - Weakness: poor on very short time series (<2 years); use simpler models (moving average) for < 6 months of data
- **Application to this project**: Default forecasting model. Always add Vietnamese public holidays to Prophet's holiday list for more accurate forecasts.
- **Added**: 2025-06-01

### [KB-002] N-BEATS: Neural Basis Expansion Analysis (2020)
- **Source**: Oreshkin et al. (2020), arXiv:1905.10437
- **Key Insights**:
  - Pure deep learning approach to time-series, outperforms traditional statistical methods on M4 competition
  - Available in `neuralforecast` library (Nixtla) — no manual feature engineering needed
  - Requires more data (≥ 2 years daily) to outperform Prophet
- **Application**: Use as upgrade option when user has 2+ years of daily data
- **Added**: 2025-06-01

### [KB-003] Nixtla's StatsForecast Library — Best Practices (2023)
- **Source**: Nixtla documentation, https://nixtlaverse.nixtla.io/statsforecast/
- **Key Insights**:
  - `AutoARIMA` automatically selects best ARIMA parameters — no manual p/d/q tuning
  - `AutoETS` handles exponential smoothing with automatic model selection
  - 20x faster than statsmodels ARIMA on same data
  - `CES` (Complex Exponential Smoothing) often beats ARIMA on retail data
- **Application**: Use `AutoARIMA` as fallback when Prophet underperforms; present forecast with confidence intervals to user
- **Added**: 2025-06-01

### [KB-004] Forecasting Principles for Small Business (Hyndman & Athanasopoulos, 2021)
- **Source**: "Forecasting: Principles and Practice" 3rd ed., https://otexts.com/fpp3/
- **Key Insights**:
  - For data with < 2 years history: use simple exponential smoothing (SES) or Holt-Winters
  - Naive seasonal model (same week last year) beats complex models on noisy retail data
  - Always evaluate with rolling-window cross-validation, not train/test split
  - MAPE is misleading when actual values near zero (common in slow-moving inventory); use RMSE instead
- **Application**: Select model complexity based on data length; warn users when forecast reliability is low (< 6 months data)
- **Added**: 2025-06-01

---

## 2. Retail & Business Analytics

### [KB-005] RFM Analysis Best Practices
- **Source**: Industry standard, widely documented in marketing analytics literature
- **Key Insights**:
  - RFM (Recency, Frequency, Monetary) is the most actionable customer segmentation for small retail
  - Score customers 1–5 on each dimension; customers scoring 5-5-5 = "Champions"
  - Champions: reward and upsell. At-risk (high F/M, low R): win-back campaigns. Low value: don't over-invest
  - Works with as few as 100 customers
- **Application**: Implement RFM as default customer segmentation when transaction history is available; explain each segment to user in plain language
- **Added**: 2025-06-01

### [KB-006] Pareto/ABC Inventory Analysis
- **Source**: Classic operations management; widely validated in retail contexts
- **Key Insights**:
  - In virtually all retail businesses, ~20% of products generate ~80% of revenue (Pareto principle)
  - ABC classification: A = top 70% revenue (focus/never stockout), B = next 20% (moderate attention), C = bottom 10% (consider discontinuing or reducing stock)
  - Apply separately to revenue contribution AND profit margin — a high-revenue item with thin margin may be category C by profit
- **Application**: Auto-classify products into A/B/C when product + revenue/profit data is present; show user their "hidden cost" items
- **Added**: 2025-06-01

### [KB-007] Seasonality Patterns in Vietnamese Retail
- **Source**: General knowledge synthesized from Vietnam retail reports (Kantar, Nielsen Vietnam)
- **Key Insights**:
  - Vietnamese retail has 3 major seasonal peaks: Tết Nguyên Đán (Jan-Feb), Back-to-school (Aug-Sep), Year-end gifts (Nov-Dec)
  - F&B businesses see weekly peaks: Friday-Sunday typically 40-60% higher than Mon-Thu
  - Weather effects: Ho Chi Minh City has dry season (Dec-Apr) and rainy season (May-Nov) — affects F&B, outdoor retail differently
  - Lunar calendar events affect demand: Rằm (15th lunar month), cúng giỗ periods
- **Application**: When forecasting, always add Vietnam-specific holidays to Prophet. Flag Tết period as unreliable for year-over-year comparison (date shifts annually)
- **Added**: 2025-06-01

### [KB-008] Gross Margin vs. Contribution Margin — When to Use Each
- **Source**: Management accounting standards
- **Key Insights**:
  - Gross margin = (Revenue - COGS) / Revenue — best for product-level profitability
  - Contribution margin = (Revenue - Variable Costs) / Revenue — better for regional/channel profitability where fixed costs are shared
  - Small businesses often confuse revenue with profit; always compute and display both
  - Loss-leading products (e.g., cheap coffee to drive foot traffic) should be flagged but not immediately recommended for removal
- **Application**: When analyzing "which region is losing money," use contribution margin if fixed cost data is available; otherwise use gross margin and clearly state the limitation
- **Added**: 2025-06-01

---

## 3. Anomaly Detection in Business Data

### [KB-009] Isolation Forest for Tabular Business Data (Liu et al., 2008)
- **Source**: Liu, Ting & Zhou (2008), "Isolation Forest," *IEEE ICDM*
- **Key Insights**:
  - Isolation Forest is unsupervised, requires no labeled anomalies — ideal for business data where anomalies are rare and unlabeled
  - Works well on multivariate data (detect anomaly considering multiple columns simultaneously)
  - `contamination` parameter: set to 0.05 (expect 5% anomalies) for general business use; reduce to 0.01 for financial fraud detection
  - Fast and scalable: handles 100,000+ rows easily
- **Application**: Flag unusual expense spikes, revenue drops, or inventory movements. Default `contamination=0.05`. Explain anomalies in terms of "which combination of factors makes this row unusual"
- **Added**: 2025-06-01

### [KB-010] Statistical Process Control (SPC) for Business Metrics
- **Source**: Quality management literature; widely applied in operations
- **Key Insights**:
  - Control charts (±3σ from rolling mean) are the simplest and most interpretable anomaly detection for time-series
  - More interpretable than ML models for non-technical users: "This month's cost is 3× higher than your normal range"
  - Use SPC for time-series anomalies; use Isolation Forest for cross-sectional anomalies (a single transaction that looks wrong vs. all others)
- **Application**: Use rolling Z-score for time-series anomalies (easy to explain); reserve Isolation Forest for detecting unusual records in transactional data
- **Added**: 2025-06-01

---

## 4. Customer & Product Segmentation

### [KB-011] K-Means Best Practices for Business Segmentation
- **Source**: Applied ML literature; sklearn documentation
- **Key Insights**:
  - Always normalize features before KMeans (StandardScaler) — unscaled revenue vs. frequency will make revenue dominate
  - Use elbow method + silhouette score to select k; for small business, k=3 or k=4 almost always produces the most actionable segments
  - PCA before KMeans helps when >5 features are used
  - Segments are meaningless without business labels — use LLM to name clusters based on their centroid values
- **Application**: Run KMeans with k=3 by default; show user 3 named segments (e.g., "Khách VIP", "Khách thường xuyên", "Khách mới") with behavioral description
- **Added**: 2025-06-01

### [KB-012] DBSCAN for Detecting Unusual Customer Patterns
- **Source**: Ester et al. (1996), "A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise"
- **Key Insights**:
  - DBSCAN finds clusters of arbitrary shape and labels outliers as noise — good for finding "unusual" customers who don't fit any normal segment
  - Does not require specifying number of clusters upfront
  - Sensitive to `eps` parameter: use k-distance graph to select
  - Better than KMeans when customer behavior is non-spherical (e.g., seasonal burst buyers)
- **Application**: Use as complementary analysis after KMeans; "These 5 customers don't fit any normal pattern — they may be wholesale buyers or automated accounts"
- **Added**: 2025-06-01

---

## 5. NL2Code & Code Generation

### [KB-013] Spider Benchmark — Text-to-SQL State of the Art
- **Source**: Yu et al. (2018), "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task"
- **Key Insights**:
  - State-of-the-art Text-to-SQL models (2024) achieve ~90% exact match on Spider — high accuracy for structured query generation
  - Key failure modes: ambiguous column names, multi-table joins, arithmetic expressions in natural language
  - For this project: prefer NL-to-Pandas over NL-to-SQL (users have flat files, not databases; pandas is more flexible)
- **Application**: When generating code, ensure column names are quoted/escaped correctly; test with intentionally ambiguous column names
- **Added**: 2025-06-01

### [KB-014] Code Generation Safety in LLM-Powered Applications
- **Source**: Multiple security research papers + OWASP LLM Top 10 (2023)
- **Key Insights**:
  - Prompt injection via user data (e.g., column name `"import os; os.system('rm -rf /')"`) is a real attack vector
  - Defense: sanitize all user-controlled strings before inserting into code templates; use AST-level validation before execution
  - RestrictedPython blocks most OS-level calls but does not block all resource exhaustion (infinite loops, memory bombs)
  - Always enforce: execution timeout (30s), memory limit (512MB), no network access inside sandbox
- **Application**: Add `ast.parse()` validation before executing generated code; sanitize all DataFrame column names before using in code strings
- **Added**: 2025-06-01

### [KB-015] Pandas Agent Design Patterns (LangChain / LlamaIndex, 2023)
- **Source**: LangChain documentation, LlamaIndex pandas query engine docs
- **Key Insights**:
  - Two approaches: (1) LLM generates code from scratch, (2) LLM fills templates — templates are more reliable and secure
  - Template approach: pre-write 20 pandas patterns, LLM selects and fills parameters
  - Always pass DataFrame schema (column names + dtypes + first 3 rows) in the prompt — dramatically improves accuracy
  - Chain-of-thought prompting ("think step by step") improves code correctness by ~15% on complex queries
- **Application**: Use template-first approach for code generation; include schema context in every LLM call; use CoT prompting
- **Added**: 2025-06-01

---

## 6. Vietnamese NLP

### [KB-016] PhoBERT: Pre-trained Language Models for Vietnamese (2020)
- **Source**: Nguyen & Nguyen (2020), "PhoBERT: Pre-trained Language Models for Vietnamese," *EMNLP Findings*
- **Link**: https://arxiv.org/abs/2003.00744
- **Key Insights**:
  - PhoBERT is the standard pre-trained BERT model for Vietnamese NLP tasks
  - `vinai/phobert-base-v2` (HuggingFace) achieves SOTA on Vietnamese NER, sentiment, classification
  - Requires Vietnamese word segmentation as preprocessing step (`underthesea` library)
  - Fine-tuning on domain-specific data (business/finance vocabulary) improves accuracy significantly
- **Application**: Use as fallback intent classifier when no LLM API key is available; may need fine-tuning on business query dataset (50–200 labeled examples)
- **Added**: 2025-06-01

### [KB-017] Vietnamese Business & Finance Vocabulary Considerations
- **Source**: Domain knowledge synthesis
- **Key Insights**:
  - Vietnamese business language mixes formal terms (doanh thu, lợi nhuận) with colloquial (tiền về, hàng chạy)
  - Code-switching common: "tháng này revenue tăng không?" — mixed Vietnamese-English
  - Numbers can use both `.` and `,` as thousands separators depending on region/person
  - Common synonyms to handle: "bán chạy" = "hot seller" = "hàng nhanh" = top-selling product
- **Application**: Build synonym dictionary for common business terms; handle mixed-language input gracefully; normalize number formats on input
- **Added**: 2025-06-01

---

## 7. Business Intelligence & Data Storytelling

### [KB-018] Storytelling with Data (Knaflic, 2015) — Core Principles
- **Source**: "Storytelling with Data" by Cole Nussbaumer Knaflic
- **Key Insights**:
  - Every chart should answer ONE question — avoid dual-purpose charts
  - Pre-attentive attributes (color, size, position) guide the eye; use color sparingly and purposefully
  - "So what?" test: every insight should have a clear business implication or recommended action
  - Context: always show comparison (vs. last period, vs. target, vs. industry)
- **Application**: Chart design rule: one chart = one question. Narrative rule: every insight must end with "vì vậy bạn nên..." (therefore you should...)
- **Added**: 2025-06-01

### [KB-019] Dashboard Design Anti-Patterns
- **Source**: Ben Shneiderman's Visual Information Seeking Mantra + industry research
- **Key Insights**:
  - "Overview first, zoom and filter, then details on demand" — the golden rule of dashboard design
  - Pie charts are poor for >4 categories; use horizontal bar charts instead
  - 3D charts consistently mislead viewers — never use them
  - Color-blind safe palettes: use colorbrewer2.org palettes; avoid red-green combinations
  - Non-technical users prefer absolute numbers (1,234 units) over percentages for counts
- **Application**: Default to horizontal bar for rankings; use line charts for time-series; never use pie for >4 items; always include absolute numbers alongside percentages
- **Added**: 2025-06-01

### [KB-020] Key Metrics for Vietnamese Small Business
- **Source**: Vietnam SME analytics reports + common accounting practices
- **Key Insights**:
  - Gross profit margin benchmark by sector: F&B 60-70%, retail goods 20-40%, services 50-70%
  - Days Sales Outstanding (DSO): how quickly customers pay — critical for cash flow management
  - Inventory Turnover = COGS / Average Inventory — low turnover = dead stock = cash trapped
  - Revenue per square meter (for physical retail) — often more informative than total revenue
- **Application**: When user analyzes profitability, auto-compute and benchmark their margin against industry norms; flag if margin is significantly below benchmark
- **Added**: 2025-06-01

---

## 8. LLM for Data Analysis

### [KB-021] Benchmarking LLMs on Tabular Data Tasks (2024)
- **Source**: Multiple benchmark papers, including "TableLlama" and "TabPFN" evaluations
- **Key Insights**:
  - GPT-4o and Claude Sonnet are best for complex multi-step data analysis reasoning
  - LLMs should never be used for arithmetic directly — always generate and execute code instead
  - LLMs excel at: schema understanding, intent parsing, narrative generation, anomaly explanation
  - LLMs fail at: precise numerical aggregation, multi-step calculations, large dataset reasoning
- **Application**: Confirms core architecture decision: LLM for NLU + narrative, Python for all numbers
- **Added**: 2025-06-01

### [KB-022] Retrieval-Augmented Generation (RAG) for Business Analytics (2023-2024)
- **Source**: Lewis et al. (2020) + multiple RAG improvement papers
- **Key Insights**:
  - RAG dramatically reduces hallucination in domain-specific knowledge generation
  - For business analytics, RAG from internal company documents (past reports, policies) + external knowledge base (this file) improves recommendation quality
  - Chunk size matters: 200-400 tokens per chunk optimal for factual retrieval; larger chunks for reasoning tasks
  - Hybrid search (dense + sparse/BM25) outperforms pure semantic search for business terminology
- **Application**: Knowledge brain retrieval uses ChromaDB (dense) + BM25 (sparse) hybrid; retrieve top-3 relevant entries before generating strategic recommendations
- **Added**: 2025-06-01

### [KB-023] LLM Cost Optimization for Production Applications
- **Source**: Various engineering blogs (Anthropic, OpenAI, community)
- **Key Insights**:
  - Caching identical prompts saves 60-80% of API costs in analytics applications (many users ask similar questions)
  - Prompt compression (remove filler words, use structured formats) reduces token count by 20-40%
  - Use smaller/faster models (Haiku, GPT-4o-mini) for intent classification; larger models only for narrative generation
  - Batch requests when possible for knowledge update operations
- **Application**: Implement prompt caching for common query types; route simple intents to lighter model; cache analytics results for identical (session, question) pairs
- **Added**: 2025-06-01

---

## Knowledge Update Log

| Date | Source | Papers/Docs Added | Topics |
|------|--------|------------------|--------|
| 2025-06-01 | Manual seed | 23 entries | Forecasting, Retail, Anomaly, Segmentation, NLP, BI, LLM |

---

## Planned Auto-Crawl Sources

```python
CRAWL_SOURCES = {
    "arxiv": {
        "topics": [
            "time series forecasting retail",
            "natural language to pandas",
            "business data analysis LLM",
            "Vietnamese NLP",
            "anomaly detection tabular data",
            "customer segmentation deep learning",
        ],
        "max_papers_per_topic": 5,
        "sort_by": "submittedDate",
    },
    "semantic_scholar": {
        "topics": [
            "retail analytics machine learning",
            "small business data analysis",
            "demand forecasting deep learning",
        ],
        "max_papers_per_topic": 5,
    },
    "documentation": [
        "https://facebook.github.io/prophet/docs/",
        "https://nixtlaverse.nixtla.io/statsforecast/",
        "https://scikit-learn.org/stable/modules/outlier_detection.html",
        "https://docs.anthropic.com/en/docs/",
        "https://huggingface.co/vinai/phobert-base-v2",
    ]
}

CRAWL_SCHEDULE = "0 2 * * 1"  # Every Monday at 2:00 AM
```

---

> **Note to Agent**: Before generating any strategic business recommendation, search this knowledge base for relevant entries using semantic similarity. Cite the KB entry number (e.g., `[KB-006]`) in your recommendation. Entries added more recently are generally more reliable for cutting-edge techniques. For stable business principles (RFM, ABC analysis), date is not a reliability factor.

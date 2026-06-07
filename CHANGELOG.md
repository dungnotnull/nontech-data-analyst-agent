# Changelog

All notable changes to the NonTech Data Analyst Agent will be documented in this file.

## [0.1.0] - 2025-06-01

### Added
- Initial project structure and documentation (CLAUDE.md, PROJECT-detail.md)
- Seed knowledge base SECOND-KNOWLEDGE-BRAIN.md with 23 research entries
- Development tracking framework in PROJECT-DEVELOPMENT-PHASE-TRACKING.md

## [0.2.0] - 2026-06-07

### Added
- **Phase 0**: Project scaffolding, Python 3.11 venv, Docker config, FastAPI health endpoint, Streamlit demo
- **Phase 1**: FileLoader with encoding detection and chunking, SchemaDetector with Vietnamese date/currency support, DataCleaner with multiple strategies
- **Phase 2**: IntentParser with rule-based VN/EN parsing + LLM fallback via litellm, 300+ line intent schema
- **Phase 3**: PythonSandbox with AST validation and multiprocess isolation, CodeGenerator with 9 analysis type templates, retry logic
- **Phase 4**: ChartRenderer with Plotly (10 chart types, bilingual), NarrativeWriter with Vietnamese/English output and recommendation engine
- **Phase 5**: Forecaster (Prophet + StatsForecast + SMA fallback), AnomalyDetector (IF/LOF/Z-score/IQR), Segmenter (KMeans/DBSCAN/RFM)
- **Phase 6**: KnowledgeUpdater with arXiv + Semantic Scholar crawling, ChromaDB vector store, BM25 + semantic hybrid search, APScheduler cron
- **Phase 7**: React frontend with Vite + TypeScript + Tailwind, Zustand state management, drag-drop upload, chat UI, settings panel
- **Phase 8**: Rate limiting, structured logging with rotation, security headers, session cleanup, multi-stage Dockerfile, sample data files

### Security
- Sandbox escape prevention via AST whitelist + multiprocess isolation
- Security headers (CORS, XSS, frame options, referrer policy)
- Rate limiting on upload and analyze endpoints
- Ephemeral session storage with 24h TTL auto-cleanup
- No raw user data sent to external LLM APIs

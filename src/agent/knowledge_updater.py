from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import re
import hashlib
import time
import threading

import httpx
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler

from src.config.settings import settings, CHROMA_DIR


class KnowledgeUpdater:
    def __init__(self):
        self.knowledge_file = Path(__file__).resolve().parent.parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"
        self.index_dir = CHROMA_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.index_dir / "knowledge_index.json"

        self._index: dict[str, Any] = self._load_index()
        self._scheduler: BackgroundScheduler | None = None
        self._lock = threading.Lock()
        self._chroma_client = None

    def _count_md_entries(self) -> int:
        try:
            if self.knowledge_file.exists():
                content = self.knowledge_file.read_text(encoding="utf-8")
                return len(re.findall(r'^### \[KB-\d+\]', content, re.MULTILINE))
        except Exception:
            pass
        return 0

    def get_status(self) -> dict[str, Any]:
        json_entries = len(self._index.get("entries", []))
        md_entries = self._count_md_entries()
        total = max(json_entries, md_entries)
        return {
            "last_update": self._index.get("last_crawl", "2025-06-01"),
            "total_entries": total,
            "json_indexed_entries": json_entries,
            "md_seed_entries": md_entries,
            "total_papers_indexed": self._index.get("total_papers", total),
            "topics_tracked": list(settings.CRAWL_SOURCES.get("arxiv", {}).get("topics", [])),
            "crawl_enabled": settings.KNOWLEDGE_CRAWL_ENABLED,
            "next_scheduled_crawl": self._index.get("next_crawl"),
        }

    def run_update(self, topics: list[str] | None = None) -> dict[str, Any]:
        if topics is None:
            topics = settings.CRAWL_SOURCES.get("arxiv", {}).get("topics", [])[:2]

        papers_added = 0
        new_papers = []

        for topic in topics:
            try:
                arxiv_papers = self._fetch_arxiv(topic, max_results=5)
                for paper in arxiv_papers:
                    if not self._is_duplicate(paper):
                        self._index_entry(paper, topic)
                        new_papers.append(paper)
                        papers_added += 1
                time.sleep(2)
            except Exception as e:
                pass

        try:
            semantic_papers = self._fetch_semantic_scholar(
                "retail analytics machine learning", max_results=3
            )
            for paper in semantic_papers:
                if not self._is_duplicate(paper):
                    self._index_entry(paper, "retail analytics")
                    new_papers.append(paper)
                    papers_added += 1
        except Exception:
            pass

        self._index["last_crawl"] = datetime.now(tz=timezone.utc).isoformat()
        self._index["total_papers"] = self._index.get("total_papers", 0) + papers_added
        self._index["next_crawl"] = (datetime.now(tz=timezone.utc) + timedelta(days=7)).isoformat()
        self._save_index()

        if new_papers:
            self._update_knowledge_md(new_papers)

        try:
            self._index_to_chromadb(new_papers)
        except Exception:
            pass

        return {
            "status": "completed",
            "papers_added": papers_added,
            "papers": [
                {"title": p.get("title", ""), "source": p.get("source", "")}
                for p in new_papers
            ],
            "message": f"Indexed {papers_added} new papers",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

    def search(
        self,
        query: str,
        top_k: int = 3,
        use_chromadb: bool = True,
    ) -> list[dict[str, Any]]:
        results = []

        if use_chromadb:
            try:
                chroma_results = self._search_chromadb(query, top_k)
                results.extend(chroma_results)
            except Exception:
                pass

        if len(results) < top_k:
            bm25_results = self._search_bm25(query, top_k)
            existing_ids = {r.get("id") for r in results}
            for r in bm25_results:
                if r.get("id") not in existing_ids:
                    results.append(r)
                    if len(results) >= top_k:
                        break

        return results[:top_k]

    def start_scheduler(self):
        if not settings.KNOWLEDGE_CRAWL_ENABLED:
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        self._scheduler = BackgroundScheduler(daemon=True)
        cron_parts = settings.KNOWLEDGE_CRAWL_SCHEDULE.split()
        self._scheduler.add_job(
            self.run_update,
            trigger=CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
            ),
            id="knowledge_update",
            replace_existing=True,
        )
        self._scheduler.start()

    def stop_scheduler(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    def summarize_paper(self, paper: dict) -> str:
        title = paper.get("title", "")
        abstract = paper.get("abstract", paper.get("summary", ""))
        source = paper.get("source", "")

        sentences = re.split(r'(?<=[.!?])\s+', abstract)
        key_sentences = [s for s in sentences if len(s.split()) > 4][:3]
        summary = " ".join(key_sentences) if key_sentences else abstract[:300]

        business_terms = [
            "revenue", "sales", "forecast", "prediction", "retail", "customer",
            "profit", "inventory", "demand", "pricing", "recommendation", "anomaly",
            "doanh thu", "dự báo", "khách hàng", "bán lẻ",
        ]
        relevance_note = ""
        abstract_lower = abstract.lower()
        matched_terms = [t for t in business_terms if t in abstract_lower]
        if matched_terms:
            relevance_note = f"Relevant for: {', '.join(matched_terms[:3])}"

        return (
            f"### {title}\n"
            f"- **Source**: {source} ({paper.get('published', paper.get('year', 'N/A'))})\n"
            f"- **Link**: {paper.get('link', paper.get('url', 'N/A'))}\n"
            f"- **Summary**: {summary}\n"
            + (f"- **Application**: {relevance_note}\n" if relevance_note else "")
            + f"- **Added**: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}\n"
        )

    def _fetch_arxiv(self, topic: str, max_results: int = 5) -> list[dict[str, Any]]:
        base_url = "http://export.arxiv.org/api/query"
        query = f"all:{topic}"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(base_url, params=params)
                if resp.status_code != 200:
                    return []

                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.text)
                ns = {
                    "atom": "http://www.w3.org/2005/Atom",
                    "arxiv": "http://arxiv.org/schemas/atom",
                }

                papers = []
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    link = entry.find("atom:id", ns)
                    published = entry.find("atom:published", ns)

                    papers.append({
                        "id": self._hash_id((title.text or "").strip()),
                        "title": (title.text or "").strip().replace("\n", " "),
                        "abstract": (summary.text or "").strip().replace("\n", " "),
                        "link": (link.text or "").strip(),
                        "published": (published.text or "")[:10] if published is not None else "",
                        "source": "arxiv",
                    })

                return papers
        except Exception:
            return []

    def _fetch_semantic_scholar(self, topic: str, max_results: int = 3) -> list[dict[str, Any]]:
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": topic,
            "limit": max_results,
            "fields": "title,abstract,year,url,externalIds",
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(base_url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                papers = []
                for item in data.get("data", []):
                    papers.append({
                        "id": self._hash_id(item.get("title", "")),
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", "") or "",
                        "link": item.get("url", ""),
                        "published": str(item.get("year", "")),
                        "source": "semantic_scholar",
                    })
                return papers
        except Exception:
            return []

    def _is_duplicate(self, paper: dict) -> bool:
        paper_id = paper.get("id", self._hash_id(paper.get("title", "")))
        for entry in self._index.get("entries", []):
            if entry.get("id") == paper_id:
                return True
        return False

    def _index_entry(self, paper: dict, topic: str):
        entry = {
            **paper,
            "topic": topic,
            "indexed_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._index.setdefault("entries", []).append(entry)

    def _update_knowledge_md(self, papers: list[dict]):
        if not papers:
            return
        new_content = "\n\n## Auto-Crawled Updates\n"
        for paper in papers:
            new_content += "\n" + self.summarize_paper(paper)

        try:
            with open(self.knowledge_file, "a", encoding="utf-8") as f:
                f.write(new_content)
        except Exception:
            pass

    def _load_index(self) -> dict[str, Any]:
        if self._index_path.exists():
            try:
                with open(self._index_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"entries": [], "last_crawl": None, "total_papers": 0}

    def _save_index(self):
        with self._lock:
            try:
                with open(self._index_path, "w", encoding="utf-8") as f:
                    json.dump(self._index, f, indent=2, ensure_ascii=False, default=str)
            except Exception:
                pass

    def _hash_id(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

    def _get_chroma_client(self):
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.PersistentClient(
                    path=str(self.index_dir / "chromadb"),
                )
            except Exception:
                self._chroma_client = False
        return self._chroma_client if self._chroma_client is not False else None

    def _index_to_chromadb(self, papers: list[dict]):
        if not papers:
            return
        client = self._get_chroma_client()
        if client is None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            collection = client.get_or_create_collection(
                name="knowledge_brain",
                metadata={"hnsw:space": "cosine"},
            )

            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            texts = [
                f"{p.get('title', '')}: {p.get('abstract', '')[:500]}"
                for p in papers
            ]
            ids = [p.get("id", self._hash_id(p.get("title", ""))) for p in papers]
            embeddings = model.encode(texts, show_progress_bar=False)

            metadatas = [
                {"title": p.get("title", ""), "source": p.get("source", ""),
                 "link": p.get("link", ""), "topic": p.get("topic", "")}
                for p in papers
            ]

            collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
            )
        except Exception:
            pass

    def _search_chromadb(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        client = self._get_chroma_client()
        if client is None:
            return []

        try:
            from sentence_transformers import SentenceTransformer

            collection = client.get_or_create_collection(name="knowledge_brain")
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            query_embedding = model.encode([query], show_progress_bar=False)

            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            output = []
            if results.get("ids") and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    output.append({
                        "id": doc_id,
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "score": 1.0 - float(results["distances"][0][i])
                        if results.get("distances") else 0.0,
                    })
            return output
        except Exception:
            return []

    def _search_bm25(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        query_terms = set(query.lower().split())
        entries = self._index.get("entries", [])
        if not entries:
            return []

        scored = []
        for entry in entries:
            title = entry.get("title", "").lower()
            abstract = entry.get("abstract", "").lower()
            text = title + " " + abstract

            score = 0.0
            for term in query_terms:
                term_clean = term.strip(".,?!;:")
                if term_clean in text:
                    tf = text.count(term_clean)
                    df = sum(1 for e in entries
                            if term_clean in (e.get("title", "") + " " + e.get("abstract", "")).lower())
                    idf = np.log((len(entries) + 1) / (df + 1)) + 1
                    score += tf * idf

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": entry.get("id", ""),
                "document": f"{entry.get('title', '')}: {entry.get('abstract', '')[:300]}",
                "metadata": {
                    "title": entry.get("title", ""),
                    "source": entry.get("source", ""),
                    "link": entry.get("link", ""),
                    "topic": entry.get("topic", ""),
                },
                "score": round(float(score), 4),
            }
            for score, entry in scored[:top_k]
        ]


_knowledge_updater_instance: KnowledgeUpdater | None = None


def get_knowledge_updater() -> KnowledgeUpdater:
    global _knowledge_updater_instance
    if _knowledge_updater_instance is None:
        _knowledge_updater_instance = KnowledgeUpdater()
    return _knowledge_updater_instance

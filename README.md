# Opsis

A fanfiction recommendation engine. The alpha version of [Siagnos](https://github.com/P-Kumar-18/Siagnos).

Opsis takes a fic you liked and finds others like it. It scrapes AO3 metadata, encodes each summary into a semantic embedding, and ranks candidates by cosine similarity blended with fandom, relationship, and popularity signals. A Groq-hosted model then writes a short explanation for each result, without touching the ranking itself.

AO3 has millions of fics and no way to search by what they actually feel like to read. Opsis fixes that with a content-based recommender built on real AO3 metadata, deployed as a working web app rather than a notebook.

It's the foundation Siagnos builds on. Siagnos adds personal taste modelling trained on individual reading behaviour; Opsis handles the similarity layer underneath it.

---

## 🚀 Current Features

- Search by AO3 **Work ID**, **URL**, or **title + author**
- On-demand ingestion for works not already in the database: scrape, clean, embed, and recommend in a single request
- Metadata-only AO3 collection; fanwork text is never stored
- Semantic summary embeddings via `sentence-transformers/all-MiniLM-L6-v2`
- Hybrid ranking: semantic similarity, fandom overlap, relationship overlap, and popularity
- Groq-generated explanation for every recommendation, with a safe fallback if the call fails
- Normalized PostgreSQL schema with idempotent, upsert-based loading
- Process-wide in-memory embedding cache, invalidated whenever new embeddings are saved
- Batched metadata and recommendation resolution instead of one query per candidate
- Custom FastAPI + Jinja2 web application
- Deployed on Render, backed by Neon PostgreSQL

---

## 🧮 Ranking & Explanations

Each summary becomes a 384-dimension vector. Candidates are retrieved by cosine similarity, then re-ranked:

```text
final_score =
    0.70 × embedding_similarity
  + 0.15 × fandom_similarity
  + 0.10 × relationship_similarity
  + 0.05 × popularity
```

Fandom and relationship overlap use Jaccard similarity; popularity is normalized kudos and bookmarks. Semantic similarity dominates on purpose, so Opsis stays a content-based recommender rather than a tag or popularity sorter.

After ranking, `ExplanationService` sends the source work and its recommendations to Groq (`openai/gpt-oss-20b`), which writes one grounded explanation per result from metadata Opsis already has. Groq never selects or re-ranks. If the call fails, a fallback explanation is used instead of dropping the recommendation.

---

## 🔄 Pipeline Overview

```text
AO3 work
  → Resolve from PostgreSQL
  → Not found? Scrape → clean → validate → normalize → insert → embed → invalidate cache
  → Retrieve source embedding
  → Cosine similarity against cached candidate embeddings
  → Batch metadata lookup
  → Hybrid re-ranking
  → Top 10 recommendations
  → Groq explanation layer
  → FastAPI response → Jinja2 / JS UI
```

- Loading is idempotent: fics upsert with `COALESCE` protection, lookup and join tables never duplicate.
- Embeddings persist behind an `EmbeddingStore` interface, pickle locally, PostgreSQL in production, cached in memory after first retrieval since remote transfer, not the similarity math, was the actual bottleneck.
- The initial bulk dataset: 7,031 fics, 1,549 fandoms, 5,584 relationships, 5,785 characters, roughly 30K freeform tags, primarily My Hero Academia. On-demand ingestion has grown the live database beyond this snapshot. See `data/README.md` for collection and reproduction details.

---

## 🧱 Project Structure

```text
Opsis/
├── src/
│   ├── main.py
│   ├── database/
│   │   └── schema.sql
│   ├── loader/
│   │   ├── config.py
│   │   ├── cleaner.py
│   │   ├── normalizer.py
│   │   ├── validator.py
│   │   ├── database.py
│   │   ├── inserter.py
│   │   └── load_ao3.py
│   ├── recommender/
│   │   ├── embedding_generator.py
│   │   ├── embedding_store.py
│   │   ├── pickle_store.py
│   │   ├── postgres_store.py
│   │   ├── similarity.py
│   │   ├── ranker.py
│   │   └── recommend.py
│   ├── services/
│   │   ├── fic_resolver.py
│   │   ├── ingestion_service.py
│   │   ├── explanation_service.py
│   │   ├── metadata.py
│   │   ├── format_author.py
│   │   └── normalize.py
│   ├── routes/
│   │   ├── index_route.py
│   │   ├── about_route.py
│   │   └── recommend_route.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── recommend.html
│   │   └── about.html
│   └── static/
│       ├── style.css
│       └── app.js
├── data/
│   ├── README.md
│   ├── scrape_ao3.py
│   ├── raw/
│   ├── invalid/
│   ├── debugging/
│   └── processed/
├── notebooks/
├── experiments/
├── requirements.txt
└── README.md
```

---

## 🛠️ Setup Instructions

### 1. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

### 2. Install dependencies

```bash
pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Set `DATABASE_URL` and `GROQ_API_KEY` in `.env`. Never commit credentials.

### 4. Load the initial dataset

```bash
python -m src.loader.load_ao3
```

### 5. Run Opsis

```bash
fastapi run ./src/main.py
```

---

## 📚 Tech Stack

- Python 3.13, FastAPI, Uvicorn, Jinja2
- PostgreSQL (psycopg 3), pandas, NumPy
- Sentence Transformers (`all-MiniLM-L6-v2`), scikit-learn
- Groq API (`openai/gpt-oss-20b`) for recommendation explanations
- cloudscraper, Beautiful Soup for AO3 collection
- Neon PostgreSQL and Render for deployment

---

## 🎯 Project Status

**Opsis is a working, deployed internship deliverable**, folded into ongoing Siagnos development going forward.

Implemented:

- [x] AO3 scraper with resume support and failure logging
- [x] Cleaning, validation, and idempotent PostgreSQL loading
- [x] MiniLM embeddings with PostgreSQL persistence and in-memory caching
- [x] Hybrid ranking (semantic + fandom + relationship + popularity)
- [x] On-demand ingestion for unseen works
- [x] Groq-generated explanations with fallback handling
- [x] FastAPI + Jinja2 web application
- [x] Render deployment on Neon PostgreSQL
- [x] End-to-end integration and performance testing (embedding cache cut candidate retrieval from ~75s to effectively 0s on repeat requests; batched resolution cut recommendation lookup from ~9s to ~1s)

Known limitations:

- No formal recommendation-quality benchmark yet, only informal similarity-score observation
- Corpus is still MHA-centered, not representative of all of AO3
- A cold or invalidated cache still needs a full remote embedding fetch; retrieval is in-memory, not a native vector index

Still planned:

- [ ] Formal precision/recall-style benchmark
- [ ] pgvector-backed retrieval
- [ ] Reader-specific taste modelling, carried forward into Siagnos

---

## 📝 License

TBD
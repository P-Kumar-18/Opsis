# Opsis

A fanfiction recommendation engine. The alpha version of [Siagnos](https://github.com/P-Kumar-18/Siagnos).

## What it does

Opsis takes a fic you liked and finds others like it. It generates embeddings from fic summaries and metadata scraped from AO3, then uses cosine similarity to surface the closest matches from a local database.

It primarily works on the semantic content of summaries while incorporating fandom, relationship, and popularity signals during reranking.

## Why this exists

AO3 has millions of fics and no way to search by what they actually feel like to read. Opsis fixes that with a content-based recommender built on real AO3 metadata.

It's the foundation Siagnos builds on. Siagnos adds personal taste modelling trained on reading behaviour. Opsis handles the similarity layer underneath it.

## Pipeline

```
AO3 CSV
  → Cleaning (comma-stripped integers, status normalization, date parsing, list deserialization)
  → Row validation
  → Invalid row export
  → Normalization (fic_id extraction from URL, duplicate removal, lookup table construction)
  → PostgreSQL insertion (fics upserted with COALESCE protection, lookup/join tables idempotent)
  → Structural validation
  → Commit

Fic summaries
  → Sentence-transformer embeddings (all-MiniLM-L6-v2)
  → Stored in data/processed/embeddings.pkl

Query fic
  → Cosine similarity against all stored embeddings
  → Top-N candidates
  → Batched metadata fetch (fandoms, relationships, popularity)
  → Weighted re-ranking (embedding 0.70, fandom 0.15, relationship 0.10, popularity 0.05)
  → Ranked recommendations
```

## Dataset

Built from roughly 7,000 fics scraped from AO3 in the My Hero Academia fandom. Metadata only: titles, summaries, tags, word counts, kudos, bookmarks. No fanwork content is stored or reproduced.

See `data/README.md` for how the dataset was collected and how to reproduce it.

## Project Structure

```
Opsis/
├── src/
│   ├── main.py                    # Future FastAPI application entry point
│   ├── database/
│   │   └── schema.sql             # fics, behaviour, 6 lookup tables, 6 join tables, 2 ENUMs
│   ├── loader/
│   │   ├── config.py              # column lists and table mappings
│   │   ├── cleaner.py             # integer/status/date/list-field cleaning
│   │   ├── normalizer.py          # fic_id extraction, dedup, lookup + join table construction
│   │   ├── validator.py           # row validation and structural integrity checks
│   │   ├── database.py            # psycopg3 connection, lookup map retrieval
│   │   ├── inserter.py            # insert_fics / insert_value_tables / insert_join_tables
│   │   └── load_ao3.py            # pipeline orchestrator
│   ├── recommender/
│   │   ├── embedding_generator.py # sentence-transformer embedding generation
│   │   ├── embedding_store.py     # EmbeddingStore abstract interface
│   │   ├── pickle_store.py        # PickleEmbeddingStore implementation
│   │   ├── similarity.py          # cosine and Jaccard similarity
│   │   ├── ranker.py              # weighted final score
│   │   └── recommend.py           # Recommender — top-level orchestration
│   ├── templates/                 # Jinja2 templates — empty
│   └── static/                    # CSS/JS — empty
├── data/
│   ├── README.md                  # explains the legal situation, how to reproduce the dataset
│   ├── scrape_ao3.py              # AO3 scraper, provided instead of the dataset itself
│   ├── raw/
│   │   └── ao3_data.csv           # gitignored
│   ├── invalid/
│   │   └── invalid_rows.csv       # gitignored 
│   ├── debugging/                 # gitignored
│   └── processed/
│       └── embeddings.pkl         # gitignored
├── notebooks/
│   └── ao3_loader_prep.ipynb      # EDA that shaped the cleaning logic
├── experiments/
│   ├── generate_embeddings.py
│   └── test_recommender.py
├── notes/
├── venv/
├── .gitignore
├── requirements.txt
└── README.md
```

## Tech stack

- Python, FastAPI, Jinja2
- HuggingFace Sentence Transformers for embeddings
- PostgreSQL (psycopg3) for fic metadata storage
- scikit-learn for cosine similarity

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run the loader (populates PostgreSQL from the scraped CSV):
```bash
python -m src.loader.load_ao3
```

Generate embeddings and get recommendations directly through Python — there's no web route yet, since `main.py` is still empty. Once FastAPI routes exist, this section will show the actual run command.

No automated tests exist yet for the loader or recommender modules.

## Status

**Loader — done:**
- AO3 scraper with cloudscraper, retry caps, failed-URL logging, resume logic
- Integer/status/date/list-field cleaning
- fic_id extraction, duplicate removal, lookup table construction
- PostgreSQL insertion with upsert and COALESCE protection
- Supports both local PostgreSQL configuration and cloud DATABASE_URL deployments.
- ~7,031 fics loaded

**Recommender — done:**
- Sentence-transformer embedding generation (all-MiniLM-L6-v2)
- Pickle-based embedding storage, built with a future pgvector migration in mind
- Cosine similarity search over the full embedding set
- Weighted ranking blending embedding similarity, fandom/relationship overlap, and popularity
- Batched database queries (4 total per recommendation call, not one per candidate)

**Not yet built:**
- FastAPI routes
- Jinja2 template rendering
- Pydantic schemas
- Automated tests

**This project is being folded into Siagnos.** The loader and recommender code now also live in the Siagnos repo, maintained in both places going forward. Opsis continues as the standalone internship deliverable until the deadline; after that, Siagnos is where ongoing development happens.

## License

TBD
# Opsis

A fanfiction recommendation engine. The alpha version of [Siagnos](https://github.com/P-Kumar-18/Siagnos).

## What it does

Opsis takes a fic you liked and finds others like it. It generates embeddings from fic summaries and metadata scraped from AO3, then uses cosine similarity to surface the closest matches from a local database.

It's not tag matching. It works on the semantic content of summaries — what the fic is actually about, not what labels someone slapped on it.

## Why this exists

Finding good fanfiction is broken. AO3 has millions of fics and no way to search by what they actually feel like to read. Opsis is a first step toward fixing that — a content-based recommender built on real AO3 metadata.

It's the foundation Siagnos builds on. Siagnos adds personal taste modelling trained on reading behaviour. Opsis does the similarity layer that sits underneath it.

## Dataset

Built from ~7,000 fics scraped from AO3 from the My Hero Academia fandom.. Metadata only — titles, summaries, tags, word counts, kudos, bookmarks. No fanwork content is stored or reproduced.

See `data/README.md` for how the dataset was collected and how to reproduce it.

## Tech stack

- Python, FastAPI, Jinja2
- HuggingFace Sentence Transformers for embeddings
- PostgreSQL for fic metadata storage
- scikit-learn for cosine similarity

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Status

Active development. Internship project — building toward a working recommender by end of July 2026.

## License

TBD
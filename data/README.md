# AO3 Fanfiction Metadata Dataset (Self-collected)

This dataset was built for Opsis, the alpha version of [Siagnos](https://github.com/P-Kumar-18/Siagnos). It contains metadata scraped from Archive of Our Own (AO3) across the My Hero Academia fandom.

## Collection

A custom scraper built with `cloudscraper` and `BeautifulSoup` collected the data directly from AO3. The scraper respects AO3's rate limits with randomised delays between requests. Before scraping at scale, the OTW Communications Committee confirmed automated collection is acceptable provided the project focuses on metadata rather than fanwork content.

The scraper is included in this folder as `scrape_ao3.py`.

## Dataset

- **Rows:** ~7,000 fics (approximately 40 failed to load and were skipped)
- **Source:** archiveofourown.org, My Hero Academia fandom
- **Format:** CSV

## Columns

| Column | Type | Description |
| --- | --- | --- |
| title | text | Fic title |
| author | text | AO3 author profile path (nullable) |
| summary | text | Author-written fic description (nullable) |
| words | integer (raw) | Total word count |
| current_chapters | integer (raw) | Chapters published at time of scrape |
| total_chapters | integer (raw) | Planned total chapters, null if ongoing |
| kudos | integer (raw) | AO3 kudos count |
| bookmarks | integer (raw) | AO3 bookmark count |
| hits | integer (raw) | AO3 hit count |
| rating | text | AO3 content rating |
| language | text | Language of the fic |
| status | text | Completed or Updated (ongoing) |
| last_date | text | Date of last update or completion |
| warning | list | Content warnings |
| category | list | Relationship categories |
| fandom | list | Fandoms tagged |
| relationship | list | Relationship tags |
| character | list | Character tags |
| freeform | list | Additional freeform tags |
| url | text | Direct AO3 link |

## Complexity

The dataset is not a pre-cleaned spreadsheet. Several columns contain Python list literals serialised as strings (warning, category, fandom, relationship, character, freeform) — each fic can have multiple values per field. Integer columns come in with comma formatting from AO3 (e.g. `"12,345"`). Summaries contain raw text with inconsistent whitespace and occasional HTML artifacts. Status values need normalisation before use. The cleaning pipeline handles all of this before the data loads into PostgreSQL.

## Copyright

This dataset contains metadata only. No fanwork content (chapter text, comments) is stored or reproduced. Copyright in the original works remains with their creators.
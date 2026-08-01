# MobiMate

MobiMate is a Sri Lankan mobile data package comparison platform. It keeps a structured, always-current catalogue of prepaid broadband packages from local telecom carriers (starting with Mobitel), exposing them through a clean REST API and preparing the ground for ML-driven package recommendations.

## What It Does

- **Scrapes** telecom carrier web pages headlessly (Selenium + Firefox + BeautifulSoup).
- **Extracts** structured package data from messy HTML tables using a Groq-hosted LLM (llama-3.3-70b-versatile) that returns clean, validated JSON.
- **Stores** packages in a lightweight SQLite database with a normalized schema (packages, apps, and a many-to-many junction table).
- **Serves** the data via a FastAPI backend with endpoints to list, insert, update, and deactivate packages.
- **Reconciles** scraped data against the live DB on each run, so newly added plans are inserted, changed plans are updated, and removed plans are deactivated automatically.

## Repository Layout

```
MobiMate/
├── Backend/              # FastAPI application
│   ├── main.py           # API routes (list/insert/update/deactivate packages, link apps)
│   ├── models.py         # SQLAlchemy models: Package, App, package_apps junction
│   └── database.py       # Engine, session factory, and SQLite connection setup
├── DB/
│   ├── init_db.py        # Creates the packages, apps, and package_apps tables
│   └── mobimate.db       # SQLite database file
├── Web Scrapers/
│   ├── scraper.py        # Headless Firefox page fetcher using Selenium + BeautifulSoup
│   ├── mobitel.py        # Mobitel-specific scrape, LLM extraction, and DB reconciliation
│   └── package_formatting.py  # Groq prompt + JSON extraction of raw tables
├── ML/                   # Reserved for future recommendation / analysis work
└── README.md
```

## Database Schema

- **packages** — the core quantitative package data: `package_name`, `carrier`, `price`, `validity_days`, `fup_gb`, `is_fup_per_day`, `anytime_data_gb`, `voice_mins`, `sms_count`, `is_data_rollover`, `is_active`.
- **apps** — master lookup of apps/bonus apps (`app_name`, `app_icon_url`), with `app_name` unique.
- **package_apps** — junction table linking packages to apps in a many-to-many relationship.

## API Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/packages/{carrier}`          | List active packages for a carrier |
| `POST` | `/insert-packages/`            | Insert new packages (batch) |
| `PUT`  | `/packages/{package_id}`       | Update one package |
| `PUT`  | `/packages/deactivate/`        | Deactivate a list of package IDs |
| `POST` | `/insert-package-apps/`        | Link packages to apps (batch) |

## Getting Started

### 1. Initialize the database

```bash
python DB/init_db.py
```

### 2. Run the backend

```bash
cd Backend
uvicorn main:app --reload
```

Interactive docs will be available at `http://localhost:8000/docs`.

### 3. Run the Mobitel scraper

Prerequisites: Python with `selenium`, `webdriver-manager`, `beautifulsoup4`, `openai`, and `python-dotenv` installed, plus a `GROQ_API_KEY` in your environment (or a `.env` file). The scraper expects the backend to be running on `localhost:8000`.

```bash
cd "Web Scrapers"
python mobitel.py
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Scraping**: Selenium, webdriver-manager, BeautifulSoup, headless Firefox
- **Extraction**: Groq API, llama-3.3-70b-versatile, OpenAI SDK
- **Future**: ML package recommendations (see `ML/`)

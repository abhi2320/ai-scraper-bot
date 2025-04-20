# AI Scraper Bot

A CLI tool that scrapes any web page (static or dynamic), uses OpenAI’s API to parse and embed its content, and stores both raw and vectorized data in a PostgreSQL + pgvector database. You can then search your scraped pages by semantic vector similarity.

---

## 📝 Table of Contents

- [Features](#features)  
- [Technical Structure](#technical-structure)  
- [Flowchart](#flowchart)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Commands](#commands)  
- [Configuration](#configuration)  
- [Architecture & Tech Stack](#architecture--tech-stack)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- **Static & Dynamic Scraping**: Detects content type via HTTP HEAD and chooses between Requests+BS4 or Playwright.  
- **AI Parsing**: Cleans text, sends to OpenAI for structured JSON extraction (summary, key points, entities).  
- **Vector Embeddings**: Uses OpenAI embeddings to vectorize page content, stored in `pgvector`.  
- **Semantic Search**: Perform cosine similarity searches across your scraped corpus.  
- **CLI**: `typer`‑powered commands for init, scrape, search, view, list.  

## Installation
# 1. Clone this repo

# 2. Create a .env in project root:

OPENAI_API_KEY=your_api_key
DATABASE_URL=postgresql://user:password@db:5432/scraper_db
EMBEDDING_MODEL=text-embedding-ada-002
COMPLETION_MODEL=gpt-4
REQUEST_TIMEOUT=30
USER_AGENT="Mozilla/5.0 (…)"
LOG_LEVEL=INFO

# 3. Build & start:

docker compose build
docker compose up -d

# 4. Initialize DB:

docker compose run --rm app init

## Docker Commands 
## Scrape a page:
docker compose run --rm app scrape https://example.com

## Force dynamic scraping:
docker compose run --rm app scrape --dynamic https://example.com

## Search your pages:
docker compose run --rm app search "quantum computing"

## View a page by ID:
docker compose run --rm app view 3

## List recent pages:
docker compose run --rm app list --limit 10

## Architecture & Tech Stack
Python 3.10

Typer for CLI

Requests & Playwright for scraping

BeautifulSoup4 for parsing

OpenAI SDK (openai / httpx)

SQLAlchemy + pgvector for vector storage

PostgreSQL (via ankane/pgvector Docker image)

Docker & Docker Compose

Rich for console tables & styling

License
MIT © Abhishek Thakur



![ChatGPT Image Apr 20, 2025, 03_16_16 PM](https://github.com/user-attachments/assets/71e3b6e1-450b-460c-acbf-71eb82447338)

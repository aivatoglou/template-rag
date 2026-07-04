# RAG Agentic Assistant

RAG-based assistant with tools. Built with Agno, pgvector and FastAPI.

## Prerequisites

- `docker` + `docker compose`
- `make`

## Setup

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

## Run

```bash
make test     # run tests
make up       # start postgres, scrape data, start API
make down     # stop containers and remove volumes
```

The API docs are available at `http://localhost:8000/docs`.

## Data Sources

Two scrapers run at startup to populate the database:

- **Ars Technica**: fetches the latest tech/science articles from the RSS feed at `feeds.arstechnica.com/arstechnica/index` (full article body via `content:encoded`)
- **BBC News**: fetches the latest world news from the RSS feed at `feeds.bbci.co.uk/news/rss.xml`

## Retrieval

The agent is responsible for deciding if any tool call is needed, depending on the user query. If a tool call happens, queries use **hybrid search**: vector similarity (pgvector) + full-text keyword search (PostgreSQL FTS), merged with **Reciprocal Rank Fusion (RRF)**. 

> **Note**: For a more accurate retrieval, a cross-encoder **reranker** after RRF would further improve result quality by scoring each candidate against the full query because RRF alone is rank-based and has no semantic understanding of the query-document pair.

## Limitations
- The number of scraped documents from each source is limited to speed up the application startup time.
- Documents are heavily truncated to reduce ingestion time. For long documents a proper chunker with chunk IDs and overlap is needed.
- PostgreSQL FTS currently uses English stemming only. For non-English documents this works sub-optimally. Ideally, we need a classifier to detect the document's language and apply the appropriate language configuration for stemming.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Send a message to the agent |
| GET | `/health` | Health check + document count |

### Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the latest developments in AI?"}'
```

Check the contents of the database:
```bash
source .env

docker exec -it template-rag-postgres-1 psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT id, title, source from documents;"
```
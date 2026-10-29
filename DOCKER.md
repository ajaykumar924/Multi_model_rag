# Docker setup

The project runs as three services: the FastAPI backend, the Vite frontend, and PostgreSQL with the pgvector extension.

## Requirements

- Docker Desktop with Docker Compose
- An `OPENAI_API_KEY` in the project-root `.env` file

The Compose file reads `OPENAI_API_KEY` and optional `LLM_MODEL`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values from `.env`. PostgreSQL defaults are for local development; use stronger credentials outside development. If you change the database credentials, use URL-safe characters in `POSTGRES_PASSWORD`.

## Start

From the project root, run:

```powershell
docker compose up --build
```

Open the frontend at <http://localhost:5173>. The backend API is at <http://localhost:8000>, with interactive documentation at <http://localhost:8000/docs>.

Uploaded files are stored in `data/uploads/`, and PostgreSQL data is kept in the `postgres_data` Docker volume. Stop the services with `Ctrl+C`, or run `docker compose down`; both preserve the database volume.

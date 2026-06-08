# Barcode Generation Backend

FastAPI backend for a KazPost-style barcode generation system.

The project currently includes the application scaffold, async database setup, migrations, seed data, and barcode number generation endpoints.

## Requirements

- Python 3.11+
- PostgreSQL

## Setup

Create and activate a virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Update `DATABASE_URL` in `.env` if your PostgreSQL username, password, host, port, or database name are different.

## Run

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Health Check

```text
GET /api/health
```

Expected response:

```json
{"status": "ok"}
```

## Migrations

Create a new migration:

```powershell
alembic revision --autogenerate -m "describe_changes"
```

Apply migrations:

```powershell
alembic upgrade head
```

Seed default data:

```powershell
python -m app.db.seed
```

## Generate Barcode Numbers

Use Swagger at `http://127.0.0.1:8000/docs` or send a request directly:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/numbers" `
  -H "Content-Type: application/json" `
  -d "{\"package_type\":\"GP\",\"quantity\":5}"
```

Example response:

```json
{
  "items": [
    "GP0000000015KZ",
    "GP0000000025KZ",
    "GP0000000035KZ",
    "GP0000000045KZ",
    "GP0000000055KZ"
  ],
  "count": 5
}
```

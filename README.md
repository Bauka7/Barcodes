# QazPostWeb

Backend-first rewrite of the legacy KazPost barcode label application.

The current project contains a FastAPI backend that generates legacy-compatible KazPost SHPI barcode numbers, stores generation history in PostgreSQL, imports legacy settings/departments, and creates downloadable PDF labels for printing.

Detailed implementation context is stored in [`PROJECT_STATE.md`](PROJECT_STATE.md). Read it first when restoring project context in a new chat or development session.

## Current Status

Implemented:

- FastAPI backend.
- Async SQLAlchemy 2.0 with PostgreSQL and asyncpg.
- Alembic migrations.
- Legacy-compatible barcode number generation.
- Per-package barcode counters with `SELECT FOR UPDATE`.
- Generated SHPI batch/history tracking.
- Department hierarchy import from legacy DBF.
- Legacy `options.ini` counter/settings import.
- PDF label preview and downloadable PDF generation.
- Print history tracking.
- Authentication with JWT access tokens.
- Roles: `admin`, `operator`, `client`.
- Audit logging for important user actions.
- Clients, range requests, and barcode range allocation foundation.
- Frontend MVP for login, departments, generation, history, search, PDF preview/download, and print history.

Not implemented yet:

- Direct OS printer control.
- Multi-label pages.
- Advanced reports/export.
- Generation from allocated ranges.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 async
- PostgreSQL
- asyncpg
- Alembic
- Pydantic v2
- Uvicorn
- python-dotenv
- dbfread
- reportlab
- passlib[bcrypt]
- python-jose[cryptography]
- python-multipart
- Vite + React + TypeScript frontend
- Axios
- React Router

## Project Structure

```text
QazPostWeb/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      utils/
      main.py
    alembic/
    alembic.ini
    requirements.txt
    README.md
  frontend/
    src/
    package.json
    vite.config.ts
  JavaCode/
  PROJECT_STATE.md
  README.md
```

`JavaCode/` is a read-only legacy reference and must not be committed or modified.

## Backend Setup

Run commands from the repository root unless noted.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create local environment file:

```powershell
Copy-Item .env.example .env
```

Set your PostgreSQL connection string in `backend/.env`:

```text
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/barcode_db
SECRET_KEY=change-this-local-development-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

Change `SECRET_KEY` to a long random private value outside local development.

## Database Setup

Apply migrations:

```powershell
alembic upgrade head
```

Seed default counters and settings:

```powershell
python -m app.db.seed
```

Create the default admin:

```powershell
python -m app.db.create_admin
```

Default local credentials are `admin` / `admin123`. Change this password immediately.

Import real legacy counters and settings from `options.ini`:

```powershell
python -m app.db.import_legacy_options
```

Import legacy departments from DBF:

```powershell
python -m app.db.import_departments
```

The range workflow also uses the same `barcode_counters` table. Approving a range request increments the package counter, but it does not create individual `GeneratedBarcode` rows yet.

## Run Backend

From `backend/`:

```powershell
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Docker Run

Docker uses its own PostgreSQL container and a separate named volume, so it does not share data with the local database on `localhost:5432`.

From the repository root:

```powershell
docker compose up --build
```

Docker services:

- Backend: `http://localhost:8000`
- Docker PostgreSQL: `localhost:5433`

The backend container applies Alembic migrations, runs seed data, creates the default admin, and adds a small dev department tree before starting Uvicorn. Local development remains unchanged: `backend/.env`, local PostgreSQL on `localhost:5432`, and local Uvicorn usage stay as before.

## Frontend Run

Start the backend first, then run the frontend from a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

The dev server proxies `/api` to `http://127.0.0.1:8000`, so no backend CORS change is needed. Default Docker/local development credentials are `admin` / `admin123` after `python -m app.db.create_admin` or Docker startup.

Optional frontend env:

```text
VITE_API_BASE_URL=/api
```

## PDF Font Setup

PDF labels use `DejaVuSans.ttf` for Cyrillic and Kazakh department names.

Place the font here:

```text
backend/assets/fonts/DejaVuSans.ttf
```

Or configure:

```text
DEJAVU_SANS_FONT_PATH=C:\path\to\DejaVuSans.ttf
```

## Important API Examples

Login:

```powershell
curl -X POST "http://127.0.0.1:8000/api/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

In Swagger, click `Authorize` and use the same username/password.

Health check:

```powershell
curl "http://127.0.0.1:8000/api/health"
```

Generate SHPI numbers:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/numbers" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"package_type\":\"KG\",\"quantity\":4,\"department_id\":50,\"notes\":\"manual test\"}"
```

Preview PDF without marking barcodes as printed:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/batches/1/pdf-preview" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -o preview.pdf
```

Generate PDF and mark batch as printed:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/batches/1/pdf" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"printer_name\":\"Zebra S4M\",\"notes\":\"first print\"}" `
  -o barcodes_batch_1.pdf
```

List generation history:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Search generated SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/search?barcode=KG010000019KZ" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

List print history:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/print-history?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Department tree:

```powershell
curl "http://127.0.0.1:8000/api/departments/tree" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Create client, admin only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/clients" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"name\":\"Test Client\",\"contact_person\":\"Ayan\",\"contact_phone\":\"+77000000000\"}"
```

Create range request:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"client_id\":1,\"package_type\":\"KG\",\"requested_quantity\":100,\"notes\":\"initial allocation\"}"
```

Approve range request, admin/operator only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests/1/approve" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"notes\":\"approved\"}"
```

List ranges, admin/operator only:

```powershell
curl "http://127.0.0.1:8000/api/ranges?package_type=KG&status=active" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Audit logs, admin only:

```powershell
curl "http://127.0.0.1:8000/api/audit-logs?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Barcode Format

Generated SHPI format:

```text
{package_type}{obl_code}{counter_6_digits}{check_digit}{country_suffix}
```

Example:

```text
KG015778998KZ
```

Rules:

- Package type must be two uppercase Latin letters.
- Package type must exist in `barcode_counters`.
- Each package type has its own counter.
- `obl_code` comes from `app_settings`.
- Default `obl_code` is `01`.
- Default `country_suffix` is `KZ`.
- Quantity must be from `1` to `1000`.
- Counter update and history insert are atomic.
- Range approval also uses `SELECT FOR UPDATE` on `barcode_counters`.
- Range approval creates a `barcode_ranges` row but does not generate SHPI records yet.

## Legacy Files

The legacy files are reference-only:

```text
C:\QazPost\JavaCode
C:\QazPost\BarCodes new\options.ini
C:\QazPost\BarCodes new\Dbf_win.dbf
```

Do not modify them from the new backend.

## Development Notes

- Keep routes thin.
- Put business logic in services.
- Use async database sessions.
- Add models to `app/models/__init__.py` so Alembic sees them.
- Do not add frontend, Docker, or printer control unless explicitly requested.
- Do not commit `backend/.env`.
- Do not commit `JavaCode/`.

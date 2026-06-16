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
- Legacy clients API, range requests, barcode range allocation, and SHPI generation from allocated ranges.
- Individual barcode lifecycle tracking.
- Admin-only SHPI Map for monitoring counters by code and region.
- Frontend MVP for login, departments, generation, history, search, PDF preview/download, and print history.

Not implemented yet:

- Direct OS printer control.
- Multi-label pages.
- Advanced reports/export.

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

The range workflow also uses the same `barcode_counters` table. Counters are tracked by `package_type` and `region_code`; existing legacy counters are stored under the configured `obl_code` region, usually `01`. Approving a range request reserves numbers by incrementing the package counter for the current `obl_code`. Generating from a range later creates `GeneratedBatch` and `GeneratedBarcode` rows with `source = "range"`.

MVP ownership is department-based. Admin sees all data, operators see their own department subtree, and client-role users see only their own department. `/api/clients` and the `clients` table remain only for legacy compatibility and are hidden from the active frontend flow.

MVP range lifecycle is intentionally simple: `active -> exhausted` or `active -> cancelled`. Expiry and renewal fields remain in the database for future use, but the backend does not auto-expire ranges and does not expose a renew endpoint. Unused numbers from cancelled ranges are not reused because allocation is forward-only.

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
VITE_API_BASE=http://127.0.0.1:8000
```

## Enterprise Auth Architecture

QazPostWeb supports backend auth modes:

- `AUTH_MODE=local`: development/testing mode. Existing username/password login and QazPostWeb JWT tokens continue to work.
- `AUTH_MODE=external` or `AUTH_MODE=keycloak`: users enter their Keycloak username/password in the normal QazPostWeb login form. The backend exchanges credentials with Keycloak, validates the returned JWT, then resolves the local QazPostWeb user by username/email.
- `AUTH_MODE=hybrid`: migration mode. Existing local JWT tokens still work, and external Keycloak JWT tokens are accepted when JWKS is configured.

Keycloak answers who the user is. QazPostWeb still answers what the user can do inside the SHPI system. After an external JWT is validated, the backend resolves the local QazPostWeb user by username, then email. If the user does not exist locally and `KEYCLOAK_AUTO_CREATE_USERS=true`, QazPostWeb creates an active passwordless local profile with `KEYCLOAK_DEFAULT_ROLE` (`client` by default). The local `users.role`, `users.department_id`, `users.client_id`, and `users.is_active` continue to control permissions and department ownership.

In Keycloak mode, local username/password login is reserved for the local admin fallback when `LOCAL_ADMIN_LOGIN_ENABLED=true`. Ordinary users authenticate with Keycloak; a QazPostWeb admin can later change their role and assign department/client ownership from the Users page.

Example production-style environment, with placeholders only:

```text
AUTH_MODE=external
KEYCLOAK_ISSUER_URI=https://keycloak.example.kz/auth/realms/qazpost
KEYCLOAK_TOKEN_URL=https://keycloak.example.kz/auth/realms/qazpost/protocol/openid-connect/token
KEYCLOAK_JWKS_URL=https://keycloak.example.kz/auth/realms/qazpost/protocol/openid-connect/certs
KEYCLOAK_CLIENT_ID=qazpost-web
KEYCLOAK_CLIENT_SECRET=
KEYCLOAK_SCOPE=openid profile email
KEYCLOAK_AUDIENCE=qazpost-web
KEYCLOAK_AUTO_CREATE_USERS=true
KEYCLOAK_DEFAULT_ROLE=client
LOCAL_ADMIN_LOGIN_ENABLED=true
DATABASE_URL=postgresql+asyncpg://user:changeme@postgres.example.kz:5432/qazpost
CORS_ORIGINS=https://qazpost-web.example.kz
```

In production, the backend would normally run in a container, Kubernetes would provide environment variables, and Ingress would expose the backend URL. Passwords, client secrets, database URLs, and private network addresses must be stored in Kubernetes Secrets or another secret manager, never in git.

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

Detailed SHPI lookup:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/KG010000019KZ/detail" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

List barcodes by lifecycle status:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/lifecycle?status=printed&limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

For MVP, SHPI lifecycle actions are intentionally limited to generation and printing.
Barcode cancel and mark-used endpoints are not exposed in the active API.

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

Legacy clients API remains available but is hidden from the MVP frontend:

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
  -d "{\"department_id\":1,\"purpose\":\"monthly labels\",\"requested_quantity\":100,\"requested_code\":\"KG\",\"notes\":\"initial allocation\"}"
```

Approve range request, admin/operator only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests/1/approve" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"approved_code\":\"KG\",\"notes\":\"approved\"}"
```

List ranges, admin/operator only:

```powershell
curl "http://127.0.0.1:8000/api/ranges?package_type=KG&status=active" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Check remaining numbers in a range:

```powershell
curl "http://127.0.0.1:8000/api/ranges/1/remaining" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Generate SHPI from an allocated range:

```powershell
curl -X POST "http://127.0.0.1:8000/api/ranges/1/generate" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"quantity\":10,\"notes\":\"range test\"}"
```

List batches generated from a range:

```powershell
curl "http://127.0.0.1:8000/api/ranges/1/batches" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Audit logs, admin only:

```powershell
curl "http://127.0.0.1:8000/api/audit-logs?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Admin SHPI Map, counter monitoring only:

```powershell
curl "http://127.0.0.1:8000/api/admin/shpi-map" `
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
- Counters are region-aware: `barcode_counters` is unique by `package_type + region_code`.
- `obl_code` comes from `app_settings`.
- Default `obl_code` is `01`.
- Default `country_suffix` is `KZ`.
- Quantity must be from `1` to `1000`.
- Counter update and history insert are atomic.
- Range approval also uses `SELECT FOR UPDATE` on `barcode_counters`.
- Direct generation and range approval select counters by package type and current `obl_code`.
- Range approval creates a `barcode_ranges` row.
- Range generation uses `SELECT FOR UPDATE` on `barcode_ranges`.
- Range generation creates `GeneratedBatch` and `GeneratedBarcode` rows linked by `range_id`.
- Operator access is limited to the operator department subtree.
- Client-role access is limited to the user's own department.
- When all numbers are consumed, range status becomes `exhausted`.
- Current MVP range statuses are `active`, `exhausted`, and `cancelled`.
- Frontend should hide renewal buttons and expiry controls for MVP.
- Barcode lifecycle status is one of `generated`, `printed`.
- New SHPI rows store `generated_by`, `generated_at`, `department_id`, and optional `range_id`.
- Printing moves `generated` barcodes to `printed` and stores `printed_by` and `printed_at`.
- Old `used`/`cancelled` columns and data remain in the database only for compatibility.

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

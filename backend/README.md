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

The department import uses `dbfread`, which is already included in `requirements.txt`.

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

Create a new migration after model changes:

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

For legacy compatibility, keep `obl_code` set to `01`. The seed script uses `01` by default and does not overwrite an existing value.

`legacy_dbf_path` is also seeded by default as `C:\QazPost\BarCodes new\Dbf_win.dbf`.

## Generate Barcode Numbers

Use Swagger at `http://127.0.0.1:8000/docs` or send a request directly:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/numbers" `
  -H "Content-Type: application/json" `
  -d "{\"package_type\":\"KG\",\"quantity\":4,\"department_id\":50,\"generated_by\":\"test_user\",\"notes\":\"manual test\"}"
```

Example response:

```json
{
  "batch_id": 1,
  "items": [
    "KG010000019KZ",
    "KG010000022KZ",
    "KG010000036KZ",
    "KG010000040KZ"
  ],
  "count": 4,
  "first_barcode": "KG010000019KZ",
  "last_barcode": "KG010000040KZ"
}
```

The request creates one generation batch and stores every generated SHPI in the database.

## Barcode History

List generation batches, newest first:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches?limit=20&offset=0"
```

Filter by package type or department:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches?package_type=KG&department_id=50"
```

Get a batch with all generated SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches/1"
```

Search one generated SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/search?barcode=KG010000019KZ"
```

## Import Departments

Import departments from the legacy DBF file:

```powershell
python -m app.db.import_departments
```

To override the DBF path manually:

```powershell
python -m app.db.import_departments "C:\QazPost\BarCodes new\Dbf_win.dbf"
```

The importer reads these DBF columns:

- `ID` -> legacy unique department code
- `ID_HI` -> parent legacy code
- `DEPNAME_PS` -> department name
- `OBL` -> region

The old Java tree uses a synthetic root with code `9999`, so the backend import creates a root department named `АО Казпочта` and attaches the top-level DBF rows under it.

## Department API

Flat list with search and pagination:

```powershell
curl "http://127.0.0.1:8000/api/departments?search=Астана&limit=20&offset=0"
```

Tree view:

```powershell
curl "http://127.0.0.1:8000/api/departments/tree"
```

## Import Legacy Options

Import legacy `options.ini` counters and settings into PostgreSQL:

```powershell
python -m app.db.import_legacy_options
```

By default, the importer reads:

```text
C:\QazPost\BarCodes new\options.ini
```

To override the file path, set `LEGACY_OPTIONS_PATH` before running the command.

Imported values:

- `MainSettings.oblCode` -> `obl_code` (always overwritten for legacy compatibility)
- `MainSettings.LastBarCodeNumberXX` -> `BarcodeCounter.package_type/current_value`
- `MainSettings.PagesQuant` -> `pages_quant`
- `MainSettings.BarCodeScale` -> `barcode_scale`
- `Font.FontBig` -> `font_big`
- `Font.FontCenter` -> `font_center`
- `Font.FontRight` -> `font_right`
- `Font.Space` -> `space`

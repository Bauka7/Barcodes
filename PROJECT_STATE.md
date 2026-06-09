# QazPostWeb Backend Project State

Last updated: 2026-06-09

## Project Overview

This project is a production-oriented FastAPI backend that replaces the old KazPost Java Swing barcode application.

The backend currently supports:

- Legacy-compatible SHPI barcode number generation.
- Per-package barcode counters stored in PostgreSQL.
- Generated barcode history and batch accounting.
- Department hierarchy import from the legacy DBF file.
- Legacy `options.ini` import for real counters and settings.
- PDF label generation for generated batches.
- Print tracking without controlling the operating system printer.

The backend intentionally does not include:

- Authentication.
- Frontend.
- Docker.
- Direct printer control.
- PDF/image generation beyond the current downloadable PDF labels.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 async
- asyncpg
- PostgreSQL
- Alembic
- Pydantic v2
- Uvicorn
- python-dotenv
- dbfread
- reportlab

## Architecture

The backend follows a clean layered structure:

```text
backend/
  app/
    main.py
    api/
      router.py
      routes/
    core/
      config.py
    db/
      database.py
      base.py
      seed.py
      import_departments.py
      import_legacy_options.py
    models/
    schemas/
    services/
    utils/
  alembic/
  alembic.ini
  requirements.txt
  README.md
```

Layer responsibilities:

- `api/routes`: thin FastAPI handlers, request/response mapping, HTTP error conversion.
- `schemas`: Pydantic request and response models.
- `services`: business logic, generation rules, imports, PDF rendering, print tracking.
- `models`: SQLAlchemy ORM models only.
- `db`: async database session setup, Alembic base metadata, seed/import CLI scripts.
- `core`: environment-based configuration.

Database sessions are async and injected into routes using `get_db_session`.

## Database Models

### AppSetting

Table: `app_settings`

Stores string key/value settings.

Important keys currently used:

- `obl_code`
- `country_suffix`
- `label_width`
- `label_height`
- `barcode_scale`
- `legacy_dbf_path`
- imported legacy optional keys such as `pages_quant`, `font_big`, `font_center`, `font_right`, `space`

### BarcodeCounter

Table: `barcode_counters`

Fields:

- `id`
- `package_type`
- `current_value`
- `created_at`
- `updated_at`

Each package type has its own counter. Generation locks the counter row using `SELECT FOR UPDATE`.

### Department

Table: `departments`

Fields:

- `id`
- `code`
- `name`
- `region`
- `parent_id`
- `department_type`
- `full_path`
- `created_at`

Used to store the imported KazPost department hierarchy from the legacy DBF file.

### GeneratedBatch

Table: `generated_batches`

Represents one generation request.

Fields:

- `id`
- `package_type`
- `quantity`
- `first_barcode`
- `last_barcode`
- `department_id`
- `generated_by`
- `source`
- `status`
- `generated_at`
- `notes`

### GeneratedBarcode

Table: `generated_barcodes`

Represents each generated SHPI.

Fields:

- `id`
- `batch_id`
- `barcode`
- `package_type`
- `department_id`
- `sequence_number`
- `printed`
- `printed_at`
- `generated_at`

`barcode` is unique to prevent duplicate SHPI records.

### PrintedBatch

Table: `printed_batches`

Represents one print/download action that marks a generated batch as printed.

Fields:

- `id`
- `generated_batch_id`
- `department_id`
- `printed_count`
- `first_barcode`
- `last_barcode`
- `printed_by`
- `printer_name`
- `status`
- `printed_at`
- `notes`

## Implemented Endpoints

All API routes are mounted under `/api`.

### Health

```http
GET /api/health
```

Returns:

```json
{"status": "ok"}
```

### Barcode Generation

```http
POST /api/barcodes/numbers
```

Request:

```json
{
  "package_type": "KG",
  "quantity": 5,
  "department_id": 50,
  "generated_by": "test_user",
  "notes": "manual test"
}
```

Response:

```json
{
  "batch_id": 1,
  "items": ["KG015779068KZ"],
  "count": 5,
  "first_barcode": "KG015779068KZ",
  "last_barcode": "KG015779104KZ"
}
```

### Barcode History

```http
GET /api/barcodes/history/batches
```

Query params:

- `limit`, default `20`, max handled in service as `100`
- `offset`, default `0`
- `package_type`, optional
- `department_id`, optional

```http
GET /api/barcodes/history/batches/{batch_id}
```

Returns batch detail with all generated barcode rows.

```http
GET /api/barcodes/history/search?barcode=KG015778998KZ
```

Returns the generated barcode record plus batch info.

### PDF Labels and Print Tracking

```http
GET /api/barcodes/batches/{batch_id}/pdf-preview
```

Generates a PDF for preview/testing. Does not update printed flags and does not create print history.

```http
POST /api/barcodes/batches/{batch_id}/pdf
```

Request:

```json
{
  "printed_by": "test_user",
  "printer_name": "Zebra S4M",
  "notes": "first print"
}
```

Returns `application/pdf` with filename:

```text
barcodes_batch_{batch_id}.pdf
```

Also:

- creates one `PrintedBatch`;
- marks all `GeneratedBarcode` rows for the batch as printed;
- sets `printed_at`.

```http
GET /api/barcodes/print-history
```

Query params:

- `limit`, default `20`, max handled in service as `100`
- `offset`, default `0`
- `department_id`, optional
- `generated_batch_id`, optional

### Departments

```http
GET /api/departments
```

Query params:

- `search`, optional
- `limit`, default `100`
- `offset`, default `0`

```http
GET /api/departments/tree
```

Returns department hierarchy.

## Barcode Generation Rules

Legacy-compatible SHPI format:

```text
{package_type}{obl_code}{counter_6_digits}{check_digit}{country_suffix}
```

Example:

```text
KG015778998KZ
```

Breakdown:

- `KG`: package type.
- `01`: oblast code from `AppSetting.obl_code`.
- `577899`: 6-digit counter value.
- `8`: calculated check digit.
- `KZ`: suffix from `AppSetting.country_suffix`.

Rules:

- `package_type` must be exactly two uppercase Latin letters.
- A package type is valid only if a matching row exists in `barcode_counters`.
- `quantity` must be between `1` and `1000`.
- `obl_code` must be exactly two digits.
- Counter values are zero-padded to six digits.
- Maximum counter value is `999999`.
- Batch generation locks the counter once and increments it by the full quantity.
- Counter update, generated batch insert, and generated barcode inserts happen in one transaction.
- Duplicate SHPI are prevented by counter locking and the unique `generated_barcodes.barcode` constraint.

Check digit algorithm:

```text
body = obl_code + counter_6_digits
weights = 8, 6, 4, 2, 3, 5, 9, 7
sum = each body digit multiplied by matching weight
remainder = sum % 11
check_digit = 11 - remainder
if check_digit == 10 -> 0
if check_digit == 11 -> 5
```

## Legacy Compatibility Decisions

The legacy Java project and runtime files are read-only references only.

Known legacy paths:

```text
C:\QazPost\JavaCode
C:\QazPost\BarCodes new\options.ini
C:\QazPost\BarCodes new\Dbf_win.dbf
```

Workspace copy of Java source:

```text
C:\Users\user\QazPostWeb\JavaCode
```

Important decisions:

- Python code must not modify legacy Java files.
- Python code must not modify legacy `options.ini` or DBF files.
- Legacy package types are imported from runtime `options.ini` counters where keys look like `LastBarCodeNumberKG`.
- Seed defaults include the real legacy catalog:
  `VC, KG, ON, AD, BP, CE, GF, RZ, AV, UP, CP, CZ, RC, CC, VR, CV, MM, UB, PP, DQ, UE, UO, CF, RW, RG, LR`
- Existing earlier package types are still seeded for compatibility:
  `GP, CO, GB, RR`
- Default `obl_code` is `01`.
- Legacy `options.ini` import intentionally overwrites `obl_code` and counter values to match legacy runtime state.
- `options.ini` loader is robust against garbage/service text before `[MainSettings]`.
- Loader tries encodings: `utf-8-sig`, `cp1251`, `utf-8`.
- DBF department import uses `Dbf_win.dbf` as read-only source and supports re-import.

## Import and Seed Commands

Run from `backend/`.

```powershell
python -m app.db.seed
```

Seeds default counters and settings without overwriting existing rows.

```powershell
python -m app.db.import_legacy_options
```

Imports legacy `options.ini` using default path or `LEGACY_OPTIONS_PATH`.

```powershell
python -m app.db.import_departments
```

Imports departments from the configured/default DBF path.

## Print System

The backend generates downloadable PDFs only. It does not call Windows printers, PDFBox, PrinterJob, or any direct OS printing API.

PDF label behavior:

- One generated barcode per PDF page.
- Page size is exactly `126 x 71` points.
- No page margin.
- Black and white only.
- Uses ReportLab Code128 barcode rendering.
- Department name is printed near the top.
- Barcode is centered in the middle.
- SHPI text is centered below the barcode.
- Text uses `DejaVuSans.ttf` so Cyrillic and Kazakh department names render correctly.
- Preferred font path is `backend/assets/fonts/DejaVuSans.ttf`; `DEJAVU_SANS_FONT_PATH` can override it.

Print tracking behavior:

- Preview endpoint generates bytes only.
- Print endpoint generates PDF bytes and updates print tracking in the same DB transaction.
- If PDF generation fails, no DB updates are made.
- If DB update fails, the request fails instead of returning success.
- A batch can currently be printed more than once; each print action creates another `PrintedBatch`.

## Migration System

Alembic is configured for SQLAlchemy metadata autogeneration.

Migration files:

- `0001_create_initial_tables.py`
- `0002_add_department_hierarchy_fields.py`
- `0003_add_generation_history.py`
- `0004_add_printed_batches.py`

Common commands from `backend/`:

```powershell
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```

When adding models, register them in `app/models/__init__.py` so Alembic can see them.

## Important Business Rules

- SHPI generation must be concurrency-safe.
- Never generate barcode numbers without locking the package counter row.
- Never update counters separately from history rows for API generation.
- Keep generation, batch history, and barcode history atomic.
- Existing seed data must not be overwritten.
- Legacy options import is the exception: it intentionally overwrites counters and `obl_code`.
- Package type validation should rely on the `barcode_counters` table, not a small hardcoded list.
- Missing counter row should return a clear error.
- Invalid input should return HTTP 400.
- Missing batch/history rows should return HTTP 404.
- Do not add authentication until explicitly requested.
- Do not add frontend until explicitly requested.
- Do not add direct printer control.

## Pending Roadmap

Likely future work:

- Improve PDF label layout after comparing with real printed labels.
- Add app setting based PDF layout controls.
- Add barcode image generation if required by frontend.
- Add print reprint rules and print status workflow.
- Add filtering/report endpoints for generated SHPI accounting.
- Add CSV/Excel export for reports.
- Add CRUD/admin endpoints for settings and counters.
- Add authentication and audit identity when requested.
- Add tests for barcode generation, imports, PDF generation, and history.
- Add frontend after backend contracts stabilize.

## Coding Conventions

- Keep route handlers thin.
- Put business logic in services.
- Use async SQLAlchemy sessions everywhere.
- Use explicit type hints.
- Keep code beginner-friendly and readable.
- Prefer small focused functions.
- Avoid Java-style monolithic classes.
- Avoid future features until they are requested.
- Do not modify legacy Java/runtime files.
- Use `.env` for local configuration.
- Do not commit `backend/.env`.
- Do not commit the `JavaCode/` folder.
- Add short comments only where they explain non-obvious logic.

## Local Startup Notes

Typical backend setup:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

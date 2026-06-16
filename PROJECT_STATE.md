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
- JWT authentication.
- Roles: `admin`, `operator`, `client`.
- Audit logging for important user actions.
- Legacy clients API, range requests, and barcode range allocation foundation.
- SHPI generation from allocated barcode ranges.
- Individual barcode lifecycle tracking.
- Admin-only SHPI Map for monitoring counters by SHPI code and region.

The backend intentionally does not include:

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
- passlib[bcrypt]
- python-jose[cryptography]
- python-multipart

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
- `region_code`
- `current_value`
- `created_at`
- `updated_at`

Each package type and region has its own counter. Generation locks the counter row using `SELECT FOR UPDATE`. Existing legacy counters are backfilled/imported under the configured `obl_code` region, usually `01`.

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
- `range_id`
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
- `range_id`
- `sequence_number`
- `printed`
- `printed_at`
- `generated_by`
- `printed_by`
- `status`
- `cancelled_at`
- `cancelled_by`
- `cancellation_reason`
- `used_at`
- `used_by`
- `usage_notes`
- `generated_at`

`barcode` is unique to prevent duplicate SHPI records.

Lifecycle statuses:

- `generated`
- `printed`

MVP note:

- active business flow uses only `generated -> printed`;
- old `used`/`cancelled` fields remain in the table for compatibility and old data;
- cancel/mark-used behavior is disabled in the active API and frontend.

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

### User

Table: `users`

Fields:

- `id`
- `username`
- `hashed_password`
- `full_name`
- `role`
- `department_id`
- `is_active`
- `created_at`
- `updated_at`

Roles are `admin`, `operator`, and `client`.

### AuditLog

Table: `audit_logs`

Fields:

- `id`
- `user_id`
- `username`
- `action`
- `entity_type`
- `entity_id`
- `ip_address`
- `user_agent`
- `details`
- `created_at`

### Client

Table: `clients`

Fields:

- `id`
- `name`
- `contact_person`
- `contact_phone`
- `email`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

### RangeRequest

Table: `range_requests`

Represents a request to allocate a numeric barcode counter range.

Fields:

- `id`
- `requester_id`
- `client_id`
- `department_id`
- `package_type`
- `requested_quantity`
- `request_type`
- `purpose`
- `requested_code`
- `approved_code`
- `decision_notes`
- `payload`
- `status`
- `handled_by`
- `handled_at`
- `notes`
- `created_at`
- `updated_at`

Statuses:

- `pending`
- `approved`
- `rejected`
- `cancelled`

### BarcodeRange

Table: `barcode_ranges`

Represents an approved numeric range reserved from the package counter.

Fields:

- `id`
- `package_type`
- `start_number`
- `end_number`
- `current_number`
- `status`
- `issued_to_client_id`
- `issued_to_department_id`
- `request_id`
- `issued_by`
- `issued_at`
- `expires_at`
- `notes`
- `created_at`
- `updated_at`

Statuses:

- `active`
- `exhausted`
- `cancelled`

Legacy/future note:

- `expired` may exist in old rows because the database still allows it.
- The MVP backend no longer auto-creates `expired` ranges and does not expose renewal.

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

### Authentication

```http
POST /api/auth/login
```

OAuth2 password flow compatible with Swagger `Authorize`.

```http
GET /api/auth/me
```

Returns the current authenticated user.

### Users

Admin only:

```http
POST /api/users
GET /api/users
GET /api/users/{user_id}
PATCH /api/users/{user_id}
```

### Audit Logs

Admin only:

```http
GET /api/audit-logs
```

### Admin SHPI Map

```http
GET /api/admin/shpi-map
```

Admin only. Returns `region_codes`, sorted `codes`, and matrix `cells` for counter monitoring. It does not calculate remaining totals, generated totals, printed totals, reports, analytics, or department statistics.

Query params:

- `limit`, default `20`, max `100`
- `offset`, default `0`
- `action`, optional
- `username`, optional

### Clients

Legacy compatibility only in the MVP. Clients are hidden from the active frontend and are not the active ownership model.

Admin/operator can read. Admin can create/update.

```http
GET /api/clients
POST /api/clients
GET /api/clients/{client_id}
PATCH /api/clients/{client_id}
```

### Range Requests

Admin can access all requests. Operators can access requests in their own department subtree. Client-role users can create/read own-department requests only.

```http
POST /api/range-requests
GET /api/range-requests
GET /api/range-requests/{request_id}
POST /api/range-requests/{request_id}/approve
POST /api/range-requests/{request_id}/reject
POST /api/range-requests/{request_id}/cancel
```

### Ranges

Admin/operator only.

```http
GET /api/ranges
GET /api/ranges/{range_id}
POST /api/ranges/{range_id}/generate
GET /api/ranges/{range_id}/remaining
GET /api/ranges/{range_id}/batches
```

### Barcode Generation

```http
POST /api/barcodes/numbers
```

Allowed roles: `admin`, `operator`, `client`.

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

Allowed roles: `admin`, `operator`.

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

### Barcode Lifecycle

```http
GET /api/barcodes/{barcode}/detail
GET /api/barcodes/lifecycle
```

Permissions:

- detail: any authenticated active user;
- lifecycle list: `admin`, `operator`.

Disabled for MVP:

- `POST /api/barcodes/{barcode}/cancel`
- `POST /api/barcodes/{barcode}/mark-used`

These actions are not exposed in the active OpenAPI/frontend. Old database columns remain for compatibility.

Lifecycle query params:

- `status`, optional;
- `package_type`, optional;
- `department_id`, optional;
- `printed`, optional;
- `limit`, default `20`, max `100`;
- `offset`, default `0`.

### PDF Labels and Print Tracking

```http
GET /api/barcodes/batches/{batch_id}/pdf-preview
```

Allowed roles: `admin`, `operator`, `client`.

Generates a PDF for preview/testing. Does not update printed flags and does not create print history.

```http
POST /api/barcodes/batches/{batch_id}/pdf
```

Allowed roles: `admin`, `operator`.

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
- sets `printed_at` and `printed_by`;
- only `generated` or already `printed` barcode rows can be printed.

```http
GET /api/barcodes/print-history
```

Allowed roles: `admin`, `operator`.

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

Department read endpoints require any authenticated active user.

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
- Range approval also locks the package counter with `SELECT FOR UPDATE`.
- Range approval increments `BarcodeCounter.current_value` and creates `BarcodeRange`.
- Range generation locks the `BarcodeRange` row with `SELECT FOR UPDATE`.
- Range generation creates `GeneratedBatch` and `GeneratedBarcode` rows linked by `range_id`.

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
- Printed barcodes get `printed = true`, `printed_at`, and `status = printed`.
- Print tracking does not overwrite lifecycle status for `used` or `cancelled` barcodes.

## Authentication and Audit

Auth uses JWT bearer access tokens.

Enterprise auth foundation:

- `AUTH_MODE=local` keeps the existing local username/password login and QazPostWeb JWT.
- `AUTH_MODE=external` or `AUTH_MODE=keycloak` lets users enter Keycloak username/password in the normal QazPostWeb login form. The backend exchanges credentials with Keycloak, validates the returned JWT, and resolves the local QazPostWeb user.
- `AUTH_MODE=hybrid` accepts local JWT and external JWT when Keycloak JWKS is configured.
- Keycloak identifies users; QazPostWeb local database controls SHPI roles and department permissions.
- External JWT roles do not replace local QazPostWeb roles.
- Valid external users are resolved locally by username or email. If missing and `KEYCLOAK_AUTO_CREATE_USERS=true`, QazPostWeb creates an active passwordless local profile with `KEYCLOAK_DEFAULT_ROLE` (`client` by default). Admin can later change role and assign department/client ownership from the Users page.
- External users may have `hashed_password = null`.
- In Keycloak mode, local password login is reserved for the local admin fallback when `LOCAL_ADMIN_LOGIN_ENABLED=true`.

Settings:

- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ALGORITHM`, default `HS256`
- `AUTH_MODE`, default `local`
- `KEYCLOAK_ISSUER_URI`
- `KEYCLOAK_TOKEN_URL`
- `KEYCLOAK_JWKS_URL`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET`
- `KEYCLOAK_SCOPE`, default `openid profile email`
- `KEYCLOAK_AUDIENCE`
- `KEYCLOAK_USERNAME_CLAIM`, default `preferred_username`
- `KEYCLOAK_EMAIL_CLAIM`, default `email`
- `KEYCLOAK_FULL_NAME_CLAIM`, default `name`
- `KEYCLOAK_AUTO_CREATE_USERS`, default `true`
- `KEYCLOAK_DEFAULT_ROLE`, default `client`
- `LOCAL_ADMIN_LOGIN_ENABLED`, default `true`
- `APP_CONTEXT_PATH`
- `SERVER_PORT`
- `CORS_ORIGINS`

Production-style environment values should be injected by container/Kubernetes configuration. Secrets, passwords, internal IPs, and private URLs must not be committed to git.

Local admin bootstrap:

```powershell
python -m app.db.create_admin
```

Default local credentials:

```text
admin / admin123
```

The default password and local `SECRET_KEY` must be changed outside local development.

Audit actions currently logged:

- `login_success`
- `login_failed`
- `user_created`
- `user_updated`
- `barcode_generated`
- `pdf_preview_generated`
- `batch_printed`
- `client_created`
- `range_request_created`
- `range_request_approved`
- `range_request_rejected`
- `range_request_cancelled`
- `range_created`
- `range_generation_started`
- `range_generation_completed`
- `range_exhausted`
- `barcode_detail_viewed`

## Barcode Lifecycle

Each `GeneratedBarcode` is now an individual lifecycle entity.

Lifecycle rules:

- new barcodes are created with status `generated`;
- generation stores `generated_by`, `generated_at`, `department_id`, `batch_id`, and optional `range_id`;
- printing moves `generated` barcodes to `printed`;
- printing stores `printed_by` and `printed_at`;
- already `printed` barcodes remain `printed`;
- active MVP statuses are only `generated` and `printed`;
- old `used`/`cancelled` columns and old rows remain for compatibility, but no active route/UI creates them.

Detailed lookup returns:

- barcode fields;
- batch info;
- range info when `range_id` exists;
- department info when `department_id` exists;
- print status;
- lifecycle status and generation/print timestamps/users.

## Range Allocation Foundation

The range workflow is a first step toward controlled client/department SHPI allocation.

Approval behavior:

- request must be `pending`;
- package counter row is locked with `SELECT FOR UPDATE`;
- `start_number = BarcodeCounter.current_value + 1`;
- `end_number = BarcodeCounter.current_value + requested_quantity`;
- `BarcodeCounter.current_value` is updated to `end_number`;
- `BarcodeRange.current_number` starts at `start_number`;
- request is marked `approved`;
- `handled_by` and `handled_at` are set;
- individual `GeneratedBarcode` rows are not created during approval.

Range generation behavior:

- request body is `{"quantity": 10, "notes": "optional"}`;
- range must be `active`;
- range row is locked with `SELECT FOR UPDATE`;
- serial numbers are consumed sequentially from `BarcodeRange.current_number`;
- generated SHPI uses the same legacy format and check digit algorithm as direct generation;
- `GeneratedBatch.source` is `range`;
- `GeneratedBatch.range_id` and `GeneratedBarcode.range_id` point to the source range;
- if any barcode insert fails, `current_number` and status changes roll back;
- when the final serial is consumed, range status becomes `exhausted`.
- MVP range lifecycle is `active -> exhausted` or `active -> cancelled`.
- Expiry/renewal fields remain in the database but are disabled in the current backend workflow.
- Unused numbers from cancelled ranges are not reused because allocation is forward-only.

Remaining endpoint:

```http
GET /api/ranges/{range_id}/remaining
```

Response shape:

```json
{
  "range_id": 1,
  "remaining": 250,
  "current_number": 1501,
  "end_number": 1750,
  "status": "active"
}
```

Range permissions:

- `admin`: all range/client operations.
- `operator`: view clients, create/view/handle requests, view ranges.
- `client`: create/view own requests only.

## Migration System

Alembic is configured for SQLAlchemy metadata autogeneration.

Migration files:

- `0001_create_initial_tables.py`
- `0002_add_department_hierarchy_fields.py`
- `0003_add_generation_history.py`
- `0004_add_printed_batches.py`
- `0005_add_auth_and_audit.py`
- `0006_add_clients_and_ranges.py`
- `0007_add_range_links_to_generated_history.py`
- `0008_add_barcode_lifecycle_fields.py`
- `0009_add_client_id_to_users.py`
- `0010_add_barcode_code_catalog.py`
- `0011_range_request_need_fields.py`
- `0012_add_range_cancellation_fields.py`
- `0013_add_generated_barcode_actor_fields.py`
- `0014_add_region_code_to_barcode_counters.py`
- `0015_prepare_users_for_external_auth.py`

Common commands from `backend/`:

```powershell
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```

When adding models, register them in `app/models/__init__.py` so Alembic can see them.

## Important Business Rules

- SHPI generation must be concurrency-safe.
- MVP frontend is department-centric: client-company management screens are hidden.
- MVP ownership is department-based.
- Admin can access all departments.
- Operator access is limited to the operator department and descendants.
- Client-role access is limited to the user's own department.
- Never generate barcode numbers without locking the package counter row.
- Never update counters separately from history rows for API generation.
- Keep generation, batch history, and barcode history atomic.
- Existing seed data must not be overwritten.
- Legacy options import is the exception: it intentionally overwrites counters and `obl_code`.
- Package type validation should rely on the `barcode_counters` table, not a small hardcoded list.
- Counter lookup for generation uses `package_type` plus the current `obl_code` as `region_code`.
- Missing counter row should return a clear error.
- MVP UI is department-centric and hides client-company management.
- Staff-created range requests may be department-only with `client_id = null`.
- If legacy `client_id` is provided, it must reference an active client.
- Client-role requests use `current_user.department_id`; request payload cannot assign another department.
- Range approval must include explicit `approved_code`; approval no longer falls back to `package_type`.
- Barcode detail, PDF, print history, generated batches, and lifecycle access are scoped by `department_id`.
- Invalid input should return HTTP 400.
- Missing batch/history rows should return HTTP 404.
- Do not add frontend until explicitly requested.
- Do not add direct printer control.
- Protected endpoint roles should stay simple until more detailed permissions are requested.

## Pending Roadmap

Likely future work:

- Improve PDF label layout after comparing with real printed labels.
- Add app setting based PDF layout controls.
- Add barcode image generation if required by frontend.
- Add print reprint rules and print status workflow.
- Add filtering/report endpoints for generated SHPI accounting.
- Revisit range expiry/renewal only if business defines a reuse policy for unused numbers.
- Add CSV/Excel export for reports.
- Add CRUD/admin endpoints for settings and counters.
- Extend authentication with password changes and finer permissions if requested.
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

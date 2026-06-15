# Barcode Generation Backend

FastAPI backend for a KazPost-style barcode generation system.

The project currently includes the application scaffold, async database setup, migrations, seed data, and barcode number generation endpoints.

It also includes authentication, roles, audit logging, legacy clients API, range requests, barcode range allocation, SHPI generation from allocated ranges, and individual SHPI lifecycle tracking.

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

The department import uses `dbfread`, and PDF label generation uses `reportlab`. Both are included in `requirements.txt`.

Authentication uses `passlib[bcrypt]`, `python-jose[cryptography]`, and `python-multipart`. These are included in `requirements.txt`.

PDF labels use `DejaVuSans.ttf` so Cyrillic and Kazakh department names render correctly. Place the font file here:

```text
backend/assets/fonts/DejaVuSans.ttf
```

Alternatively, set `DEJAVU_SANS_FONT_PATH` to the full path of `DejaVuSans.ttf`.

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Update `DATABASE_URL` in `.env` if your PostgreSQL username, password, host, port, or database name are different.

For local development, `.env.example` includes a placeholder `SECRET_KEY`. In production, replace it with a long random secret and keep it private.

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

Create the default admin user:

```powershell
python -m app.db.create_admin
```

Default credentials:

```text
username: admin
password: admin123
```

Change this password immediately after first login.

For legacy compatibility, keep `obl_code` set to `01`. The seed script uses `01` by default and does not overwrite an existing value.

`legacy_dbf_path` is also seeded by default as `C:\QazPost\BarCodes new\Dbf_win.dbf`.

## Authentication

Login uses OAuth2 password flow and works with the Swagger `Authorize` button.

1. Run `python -m app.db.create_admin`.
2. Open `http://127.0.0.1:8000/docs`.
3. Click `Authorize`.
4. Enter username `admin` and password `admin123`.
5. Use protected endpoints from Swagger.

Login with curl:

```powershell
curl -X POST "http://127.0.0.1:8000/api/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

Example protected request:

```powershell
curl "http://127.0.0.1:8000/api/auth/me" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Roles:

- `admin`: users, audit logs, generation, history, print.
- `operator`: own department subtree for range requests, ranges, generation, barcode history, PDF preview, PDF print, and print history.
- `client`: own department only for requests, ranges, generation, PDF preview/download, and own history.

## Generate Barcode Numbers

Use Swagger at `http://127.0.0.1:8000/docs` after authorization or send a request directly:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/numbers" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"package_type\":\"KG\",\"quantity\":4,\"department_id\":50,\"notes\":\"manual test\"}"
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
curl "http://127.0.0.1:8000/api/barcodes/history/batches?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Filter by package type or department:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches?package_type=KG&department_id=50" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Get a batch with all generated SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/batches/1" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Search one generated SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/history/search?barcode=KG010000019KZ" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Barcode Lifecycle

Detailed lookup for one SHPI:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/KG010000019KZ/detail" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

List generated barcodes by lifecycle:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/lifecycle?status=printed&limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Filters:

- `status`: `generated`, `printed`
- `package_type`
- `department_id`
- `printed`
- `limit`
- `offset`

For MVP, barcode cancel and mark-used endpoints are not exposed in the active API.

Lifecycle rules:

- new barcodes start as `generated`;
- printing changes `generated` barcodes to `printed`;
- generation stores `generated_by`, `generated_at`, `department_id`, and optional `range_id`;
- printing stores `printed_by` and `printed_at`;
- old `used`/`cancelled` columns and data remain only for compatibility.

## PDF Labels

Before generating PDF labels, make sure `DejaVuSans.ttf` exists at `backend/assets/fonts/DejaVuSans.ttf` or configure `DEJAVU_SANS_FONT_PATH`.

Preview a generated batch as PDF without changing print status:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/batches/1/pdf-preview" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -o preview.pdf
```

Generate a downloadable PDF and mark the batch barcodes as printed:

```powershell
curl -X POST "http://127.0.0.1:8000/api/barcodes/batches/1/pdf" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"printer_name\":\"Zebra S4M\",\"notes\":\"first print\"}" `
  -o barcodes_batch_1.pdf
```

The backend does not control the OS printer. It returns a PDF file for the user or frontend to print.

Print history:

```powershell
curl "http://127.0.0.1:8000/api/barcodes/print-history?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Audit logs, admin only:

```powershell
curl "http://127.0.0.1:8000/api/audit-logs?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Legacy Clients

Clients are hidden from the MVP frontend. These endpoints remain for legacy compatibility and should not be used by the active department-based workflow.

List clients, admin/operator:

```powershell
curl "http://127.0.0.1:8000/api/clients?limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Create client, admin only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/clients" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"name\":\"Test Client\",\"contact_person\":\"Ayan\",\"contact_phone\":\"+77000000000\"}"
```

Update client, admin only:

```powershell
curl -X PATCH "http://127.0.0.1:8000/api/clients/1" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"notes\":\"updated\"}"
```

## Range Requests and Ranges

Create a range request:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"department_id\":1,\"purpose\":\"monthly labels\",\"requested_quantity\":100,\"requested_code\":\"KG\",\"notes\":\"initial allocation\"}"
```

List range requests:

```powershell
curl "http://127.0.0.1:8000/api/range-requests?status=pending" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Approve a range request, admin/operator only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests/1/approve" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"approved_code\":\"KG\",\"notes\":\"approved\"}"
```

Reject a range request, admin/operator only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests/1/reject" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"notes\":\"not enough details\"}"
```

Cancel a range request, admin/operator only:

```powershell
curl -X POST "http://127.0.0.1:8000/api/range-requests/1/cancel" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d "{\"notes\":\"cancelled manually\"}"
```

List active ranges, admin/operator only:

```powershell
curl "http://127.0.0.1:8000/api/ranges?package_type=KG&status=active" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Approval behavior:

- locks `BarcodeCounter` with `SELECT FOR UPDATE`;
- sets `start_number = current_value + 1`;
- sets `end_number = current_value + requested_quantity`;
- updates `BarcodeCounter.current_value` to `end_number`;
- creates one `BarcodeRange`;
- marks the request as `approved`;
- does not create individual `GeneratedBarcode` rows yet.

Range generation behavior:

- locks `BarcodeRange` with `SELECT FOR UPDATE`;
- generates legacy-compatible SHPI from `BarcodeRange.current_number`;
- creates one `GeneratedBatch` with `source = "range"`;
- creates one `GeneratedBarcode` row for every generated SHPI;
- links generated batch and barcode rows to `range_id`;
- increments `BarcodeRange.current_number`;
- sets range status to `exhausted` when all numbers are consumed.

MVP ownership:

- admin can access all departments and data;
- operator can access own department and descendants;
- client can access only own department;
- generated batches, generated barcodes, ranges, PDF preview/print, and print history are scoped by `department_id`.

MVP range lifecycle:

- active ranges can generate SHPI;
- active ranges can be cancelled by admin/operator;
- exhausted ranges cannot be cancelled;
- expiry/renewal fields remain in the database for future use, but the backend does not auto-expire ranges;
- `POST /api/ranges/{range_id}/renew` is not exposed in the active API;
- unused numbers are not reused because allocation is forward-only;
- frontend should hide renewal buttons and expiry controls.

Check remaining numbers:

```powershell
curl "http://127.0.0.1:8000/api/ranges/1/remaining" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Generate SHPI from a range, admin/operator only:

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
curl "http://127.0.0.1:8000/api/departments?search=Астана&limit=20&offset=0" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Tree view:

```powershell
curl "http://127.0.0.1:8000/api/departments/tree" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
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

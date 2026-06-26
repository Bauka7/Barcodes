# QazPostWeb database schema overview

This document describes the current schema used by QazPostWeb for KazPost SHPI/barcode generation. It is based on `docs/database/barcode_schema.sql`, SQLAlchemy models, and Alembic migrations.

No real production data, secrets, connection strings, or credentials are included here.

## Table groups

| Group | Tables | Purpose |
| --- | --- | --- |
| Reference data | `departments`, `clients`, `barcode_code_catalog`, `app_settings` | Stable or configurable data used by business workflows. |
| Operational data | `users`, `range_requests`, `barcode_ranges`, `barcode_counters` | Access control and active SHPI allocation workflows. |
| Generated data | `generated_batches`, `generated_barcodes`, `printed_batches` | Barcode generation, barcode rows, and print history. |
| Audit data | `audit_logs` | Security and business action trail. |
| Migration metadata | `alembic_version` | Alembic migration state. |

## Tables

### `alembic_version`

Purpose: Alembic migration version marker.

Important columns:

- `version_num` - current Alembic revision, primary key.

### `app_settings`

Purpose: key/value application settings, including legacy settings imported or mirrored from the previous barcode system.

Important columns:

- `id` - primary key.
- `key` - unique setting name.
- `value` - setting value as text.
- `created_at` - timestamp when the setting row was created.

Constraints and indexes:

- Unique constraint on `key`.

Business notes:

- This table can hold legacy defaults such as old SHPI behavior.
- It should not contain secrets in committed dumps or documentation.

### `audit_logs`

Purpose: audit trail for user and system actions.

Important columns:

- `id` - primary key.
- `user_id` - optional link to `users.id`; kept nullable so logs survive user deletion.
- `username` - copied username string for historical readability.
- `department_id` - optional department scope for department-based audit.
- `action` - action name.
- `entity_type` and `entity_id` - affected business object.
- `ip_address`, `user_agent` - request context.
- `details` - additional action details as text.
- `created_at` - event timestamp.

Relationships:

- `audit_logs.user_id` -> `users.id`.
- `audit_logs.department_id` -> `departments.id`.

Indexes:

- `user_id`, `username`, `action`, `created_at`, `department_id`, and `(department_id, created_at)`.

Business notes:

- Admins can use this table for global audit review.
- Operators should only see audit records inside their department subtree.
- Clients should only see audit records for their own department if audit is exposed to them.

### `barcode_code_catalog`

Purpose: catalog of barcode/package codes that can be available, active, reserved, blocked, or deprecated.

Important columns:

- `id` - primary key.
- `code` - unique business code.
- `name` - display name.
- `category` - grouping/category.
- `status` - lifecycle status.
- `owner` - owner or responsible unit.
- `notes` - free-form notes.
- `created_at`, `updated_at` - timestamps.

Constraints and indexes:

- Unique index on `code`.
- Index on `status`.
- Check constraint limits `status` to `available`, `active`, `reserved`, `blocked`, `deprecated`.

Business notes:

- This is reference/catalog data.
- `package_type` values in generation tables are logical references to barcode/package codes, but the current database schema does not declare a foreign key from `package_type` to this catalog.

### `barcode_counters`

Purpose: stores the current numeric counter for each SHPI package type and region code pair.

Important columns:

- `id` - primary key.
- `package_type` - SHPI package prefix/type, for example values such as `AD`, `GP`, `CE`, etc.
- `region_code` - official SHPI region code.
- `current_value` - last consumed counter value.
- `created_at`, `updated_at` - timestamps.

Constraints and indexes:

- Unique constraint on `(package_type, region_code)`.

Business notes:

- This table is operational state and must be updated transactionally.
- SHPI generation should lock the matching counter row before incrementing.
- Official SHPI region codes are maintained in backend code, not in a database lookup table.
- Existing legacy `01` counters must remain unchanged during migrations and imports.
- New official region counters may be created lazily by application logic when a valid official region is first used.

### `barcode_ranges`

Purpose: an approved and issued range of SHPI sequence numbers.

Important columns:

- `id` - primary key.
- `package_type` - SHPI package type for the range.
- `region_code` - SHPI region code stored at approval/issue time.
- `start_number`, `end_number` - allocated inclusive sequence range.
- `current_number` - next/current sequence position inside the range.
- `status` - range state: active, exhausted, expired, or cancelled.
- `issued_to_client_id` - optional client owner.
- `issued_to_department_id` - department receiving the range.
- `request_id` - original `range_requests.id`, when created from a request.
- `issued_by` - approving/issuing user.
- `issued_at`, `expires_at` - lifecycle timestamps.
- `cancelled_by`, `cancelled_at`, `cancellation_reason` - cancellation metadata.
- `notes`, `created_at`, `updated_at` - additional metadata.

Relationships:

- `issued_to_client_id` -> `clients.id`.
- `issued_to_department_id` -> `departments.id`.
- `request_id` -> `range_requests.id`.
- `issued_by` -> `users.id`.
- `cancelled_by` -> `users.id`.

Constraints and indexes:

- `end_number >= start_number`.
- `current_number` must stay between `start_number` and `end_number`.
- Check constraint limits `status` to `active`, `exhausted`, `expired`, `cancelled`.
- Indexes on package type, region code, status, request, client, department, and issuing user.

Business notes:

- `region_code` is the source of truth for generation from a range once the range is issued.
- Old ranges may have `region_code = NULL`; application logic keeps backward compatibility by resolving from department settings or legacy defaults.
- Department SHPI mapping changes after approval should not alter the region used by an already-issued range.

### `clients`

Purpose: legacy/client organization table used by client-scoped users and range ownership.

Important columns:

- `id` - primary key.
- `name` - unique client name.
- `contact_person`, `contact_phone`, `email` - contact details.
- `is_active` - active/inactive flag.
- `notes`, `created_at`, `updated_at` - metadata.

Relationships:

- Referenced by `users.client_id`, `range_requests.client_id`, and `barcode_ranges.issued_to_client_id`.

Business notes:

- In the current department-scoped access model, department ownership is usually more important than client ownership.

### `departments`

Purpose: FilPassport/imported department tree and SHPI regional mapping.

Important columns:

- `id` - primary key.
- `code` - unique internal department code.
- `external_id` - optional external FilPassport identifier.
- `name` - department name.
- `region` - human-readable region/area name.
- `parent_id` - self-reference for department hierarchy.
- `department_type` - department classification.
- `full_path` - denormalized path for hierarchy display/search.
- `shpi_region_code` - official two-digit SHPI region code assigned or inherited during import.
- `is_active` - active/inactive flag.
- `created_at` - creation timestamp.

Relationships:

- `departments.parent_id` -> `departments.id`.
- Referenced by `users`, `range_requests`, `barcode_ranges`, `generated_batches`, `generated_barcodes`, `printed_batches`, and `audit_logs`.

Constraints and indexes:

- Unique constraint/index on `code`.
- Unique index on `external_id`.
- Indexes on `parent_id` and `shpi_region_code`.

Business notes:

- Department hierarchy is central to role scope:
  - `admin`: all departments.
  - `operator`: own department subtree.
  - `client`: own department only.
- `shpi_region_code` stores the official SHPI mapping used for range approval and fallback generation.
- There is no separate region lookup table in the current schema.

### `generated_batches`

Purpose: generation batch header for a set of generated SHPI barcodes.

Important columns:

- `id` - primary key.
- `package_type` - SHPI package type.
- `quantity` - number of barcodes generated.
- `first_barcode`, `last_barcode` - visible range boundaries.
- `department_id` - department context.
- `range_id` - source barcode range when generation is range-based.
- `generated_by` - username or external identity string.
- `source` - generation source, such as API or range workflow.
- `status` - batch status.
- `generated_at` - generation timestamp.
- `notes` - optional notes.

Relationships:

- `department_id` -> `departments.id`.
- `range_id` -> `barcode_ranges.id`.
- One `generated_batches` row has many `generated_barcodes`.
- One `generated_batches` row can have many `printed_batches`.

Indexes:

- `department_id`, `generated_at`, `package_type`, `range_id`.

### `generated_barcodes`

Purpose: individual generated SHPI barcode rows.

Important columns:

- `id` - primary key.
- `batch_id` - owning generation batch.
- `barcode` - unique full barcode string.
- `package_type` - package type used in the barcode.
- `department_id` - department context.
- `range_id` - source range, when generated from a range.
- `sequence_number` - numeric sequence component.
- `status` - generated, printed, used, or cancelled.
- `printed`, `printed_at`, `printed_by` - print state.
- `generated_at`, `generated_by` - generation metadata.
- `used_at`, `used_by`, `usage_notes` - usage metadata.
- `cancelled_at`, `cancelled_by`, `cancellation_reason` - cancellation metadata.

Relationships:

- `batch_id` -> `generated_batches.id`.
- `department_id` -> `departments.id`.
- `range_id` -> `barcode_ranges.id`.

Constraints and indexes:

- Unique index on `barcode`.
- Check constraint limits `status` to `generated`, `printed`, `used`, `cancelled`.
- Indexes on batch, department, package type, range, and status.

Business notes:

- This is generated operational history.
- For range-based generation, the region should come from `barcode_ranges.region_code`.

### `printed_batches`

Purpose: print event/history table for generated barcode batches.

Important columns:

- `id` - primary key.
- `generated_batch_id` - printed generation batch.
- `department_id` - department context.
- `printed_count` - number of labels printed.
- `first_barcode`, `last_barcode` - printed boundaries.
- `printed_by`, `printer_name` - print actor/context.
- `status` - print status.
- `printed_at` - print timestamp.
- `notes` - optional notes.

Relationships:

- `generated_batch_id` -> `generated_batches.id`.
- `department_id` -> `departments.id`.

Indexes:

- `generated_batch_id`, `department_id`, `printed_at`.

### `range_requests`

Purpose: request workflow for issuing barcode ranges.

Important columns:

- `id` - primary key.
- `requester_id` - user who created the request.
- `client_id` - optional client context.
- `department_id` - requesting/target department.
- `package_type` - requested SHPI package type.
- `requested_quantity` - requested count.
- `request_type` - request category, default `issue_range`.
- `payload` - extra request data as text.
- `status` - pending, approved, rejected, or cancelled.
- `handled_by`, `handled_at` - operator/admin decision metadata.
- `purpose` - business purpose.
- `requested_code`, `approved_code` - package/code request fields.
- `decision_notes`, `notes` - free-form notes.
- `created_at`, `updated_at` - timestamps.

Relationships:

- `requester_id` -> `users.id`.
- `client_id` -> `clients.id`.
- `department_id` -> `departments.id`.
- `handled_by` -> `users.id`.
- Referenced by `barcode_ranges.request_id`.

Constraints and indexes:

- Check constraint limits `status` to `pending`, `approved`, `rejected`, `cancelled`.
- Indexes on requester, client, department, handler, package type, and status.

Business notes:

- Clients create requests for their own department.
- Operators approve requests within their department subtree.
- Admins can review and handle all requests.

### `users`

Purpose: local user record and role/department/client mapping.

Important columns:

- `id` - primary key.
- `username` - unique username or external identity name.
- `hashed_password` - nullable because external authentication may be used.
- `full_name`, `email`, `phone` - user details.
- `role` - `admin`, `operator`, or `client`.
- `department_id` - department scope root.
- `client_id` - optional legacy/client organization mapping.
- `is_active` - active/inactive flag.
- `created_at`, `updated_at` - timestamps.

Relationships:

- `department_id` -> `departments.id`.
- `client_id` -> `clients.id`.
- Referenced by `range_requests`, `barcode_ranges`, and `audit_logs`.

Constraints and indexes:

- Unique index on `username`.
- Check constraint limits `role` to `admin`, `operator`, `client`.
- Indexes on role, department, client, email, and username.

Business notes:

- Role and department are the main basis for backend authorization scope.
- Nullable `hashed_password` supports Keycloak/external-auth users.

## SHPI region mapping

The current schema stores SHPI region code in three places:

- `departments.shpi_region_code` - official region assigned to a department, typically through FilPassport import and inheritance.
- `barcode_ranges.region_code` - region fixed at range approval/issue time.
- `barcode_counters.region_code` - region dimension for package counters.

Official SHPI region codes are handled by backend code, not by a database table. The known business set is `01`-`20`, plus `30` and `34`.

Important behavior:

- New range approval resolves the target department region once and stores it on `barcode_ranges.region_code`.
- Range-based generation should use `barcode_ranges.region_code` as source of truth.
- Old ranges with `region_code IS NULL` remain compatible through application fallback logic.
- Counter rows are unique per `(package_type, region_code)`.

## Main business relationships

- A `department` can have a parent department and many child departments.
- A `user` belongs to one department and may belong to one client.
- A `user` creates a `range_request`.
- An admin/operator handles a `range_request`.
- An approved `range_request` can create a `barcode_range`.
- A `barcode_range` belongs to a department and optionally a client.
- A `barcode_range` stores the fixed SHPI `region_code` used for generation.
- A `barcode_counter` tracks the current sequence for a `(package_type, region_code)` pair.
- A `generated_batch` groups generated barcode rows.
- A `generated_barcode` belongs to a generated batch and can come from a barcode range.
- A `printed_batch` records printing for a generated batch.
- `audit_logs` records important actions with optional user and department scope.

## Relationship notes not fully enforced by foreign keys

- `package_type` appears in `barcode_counters`, `barcode_ranges`, `range_requests`, `generated_batches`, and `generated_barcodes`. It is a logical business code, but there is no database-level foreign key to `barcode_code_catalog.code`.
- `barcode_counters.region_code` and `departments.shpi_region_code` are logical SHPI region codes. There is no database-level region table.
- `generated_by`, `printed_by`, `cancelled_by`, and `used_by` fields in generated/printed tables are stored as strings in some places, not always as foreign keys to `users.id`.


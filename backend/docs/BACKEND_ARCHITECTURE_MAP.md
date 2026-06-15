# Backend architecture map

Документ для быстрого понимания backend-а QazPostWeb.
Без истории проекта. Только что есть сейчас в коде, где лежит и что куда сохраняется.

## 1. Из чего состоит backend

Backend лежит в `backend/app`.

Главные папки:

| Папка | Для чего |
|---|---|
| `api/routes` | HTTP endpoints. Здесь видно URL, метод, роли, request/response. |
| `schemas` | Pydantic-схемы. Это контракт API: что endpoint принимает и возвращает. |
| `models` | SQLAlchemy-модели. Это таблицы базы данных. |
| `services` | Бизнес-логика: генерация ШПИ, диапазоны, PDF, печать, lifecycle. |
| `core` | JWT, пароль, настройки. |
| `db` | Подключение к базе, seed/import скрипты. |
| `alembic/versions` | Миграции базы. |

Главный вход FastAPI:

```text
backend/app/main.py
```

Главный router:

```text
backend/app/api/router.py
```

Все API имеют prefix:

```text
/api
```

Например route `/auth/login` реально доступен как:

```text
POST /api/auth/login
```

## 2. Роли

В системе есть 3 роли:

| Роль | Что делает |
|---|---|
| `admin` | Полный доступ: users, clients, audit, ranges, requests, barcodes. |
| `operator` | Рабочий доступ: генерация, заявки, диапазоны, клиенты на чтение, печать, поиск. Нет управления users/audit. |
| `client` | Видит только свою организацию: свои заявки, свои диапазоны, свои партии и PDF. |

Проверка ролей лежит здесь:

```text
backend/app/services/auth_service.py
```

Используется так:

```python
current_user: User = Depends(require_roles("admin", "operator"))
```

Если роль не подходит, backend возвращает:

```text
403 Not enough permissions.
```

Если JWT неправильный или user inactive:

```text
401 Could not validate credentials.
```

## 3. Auth

Файлы:

```text
backend/app/api/routes/auth.py
backend/app/services/auth_service.py
backend/app/core/security.py
```

### POST /api/auth/login

Роли: публичный endpoint.

Важно: принимает не JSON, а form-urlencoded.

Request:

```text
username=admin
password=admin123
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Что делает:

1. Ищет user по username.
2. Проверяет `is_active`.
3. Проверяет password через bcrypt.
4. Создает JWT.
5. Пишет audit log:
   - `login_success`
   - или `login_failed`

### GET /api/auth/me

Роли: любой залогиненный user.

Response:

```json
{
  "id": 1,
  "username": "admin",
  "full_name": null,
  "role": "admin",
  "department_id": null,
  "client_id": null,
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

Frontend после login должен вызвать `/api/auth/me`, чтобы узнать роль и client_id.

## 4. Таблицы базы

Модели лежат здесь:

```text
backend/app/models/
```

### users

Файл:

```text
backend/app/models/user.py
```

Для чего:

Пользователи системы.

Главные поля:

| Поле | Значение |
|---|---|
| `username` | Логин. Уникальный. |
| `hashed_password` | Хеш пароля. |
| `role` | `admin`, `operator`, `client`. |
| `department_id` | Отделение пользователя, если нужно. |
| `client_id` | Организация клиента. Для role=`client` обязательно. |
| `is_active` | Можно ли логиниться. |

### clients

Файл:

```text
backend/app/models/client.py
```

Для чего:

Организации-клиенты, которым выдаются диапазоны.

Главные поля:

| Поле | Значение |
|---|---|
| `name` | Название клиента. Уникальное. |
| `contact_person` | Контактное лицо. |
| `contact_phone` | Телефон. |
| `email` | Email. |
| `is_active` | Активен ли клиент. |

### departments

Файл:

```text
backend/app/models/department.py
```

Для чего:

Отделения Казпочты. Есть дерево через `parent_id`.

Главные поля:

| Поле | Значение |
|---|---|
| `code` | Код отделения. |
| `name` | Название. |
| `region` | Регион. |
| `parent_id` | Родительское отделение. |
| `department_type` | Тип отделения. |
| `full_path` | Полный путь в дереве. |

### barcode_code_catalog

Файл:

```text
backend/app/models/barcode_code_catalog.py
```

Для чего:

Справочник двухбуквенных кодов ШПИ: `CC`, `KG`, `ON` и т.д.

Статусы:

```text
available, active, reserved, blocked, deprecated
```

При одобрении заявки backend разрешает брать код только если status:

```text
available или active
```

Если код был `available`, он становится `active`.

### barcode_counters

Файл:

```text
backend/app/models/barcode_counter.py
```

Для чего:

Глобальный счетчик по каждому package_type.

Пример:

```text
package_type = CC
current_value = 359
```

Следующая генерация начнется с `360`.

Важно:

При выдаче диапазона счетчик сразу сдвигается вперед на весь размер диапазона.
При генерации без диапазона счетчик сдвигается на количество сгенерированных кодов.

### range_requests

Файл:

```text
backend/app/models/range_request.py
```

Для чего:

Заявки на диапазон ШПИ.

Статусы:

```text
pending, approved, rejected, cancelled
```

Главные поля:

| Поле | Значение |
|---|---|
| `requester_id` | Кто создал заявку. |
| `client_id` | Для какого клиента заявка. |
| `department_id` | Отделение. |
| `requested_quantity` | Сколько номеров нужно. |
| `requested_code` | Желаемый код, если клиент указал. |
| `approved_code` | Код, который назначил admin/operator. |
| `status` | Статус заявки. |
| `handled_by` | Кто обработал заявку. |
| `handled_at` | Когда обработал. |
| `decision_notes` | Комментарий решения. |

### barcode_ranges

Файл:

```text
backend/app/models/barcode_range.py
```

Для чего:

Выданный диапазон номеров клиенту или отделению.

Статусы:

```text
active, exhausted, expired, cancelled
```

Главные поля:

| Поле | Значение |
|---|---|
| `package_type` | Код: `CC`, `KG`, и т.д. |
| `start_number` | Первый номер внутри диапазона. |
| `end_number` | Последний номер. |
| `current_number` | Следующий номер, который будет использован. |
| `issued_to_client_id` | Клиент, которому выдали диапазон. |
| `issued_to_department_id` | Отделение. |
| `request_id` | Из какой заявки создан диапазон. |
| `issued_by` | Кто выдал. |
| `expires_at` | Срок действия. |
| `cancellation_reason` | Причина отмены. |

### generated_batches

Файл:

```text
backend/app/models/generated_batch.py
```

Для чего:

Партия генерации. Одна генерация = один batch.

Главные поля:

| Поле | Значение |
|---|---|
| `package_type` | Код ШПИ. |
| `quantity` | Сколько ШПИ создано. |
| `first_barcode` | Первый ШПИ в партии. |
| `last_barcode` | Последний ШПИ. |
| `department_id` | Отделение. |
| `range_id` | Из какого диапазона создано. Может быть null при старом direct-flow. |
| `generated_by` | Username генератора. |
| `source` | `api` или `range`. |
| `status` | Сейчас обычно `generated`. |

### generated_barcodes

Файл:

```text
backend/app/models/generated_barcode.py
```

Для чего:

Каждый конкретный ШПИ внутри партии.

Статусы:

```text
generated, printed, used, cancelled
```

Главные поля:

| Поле | Значение |
|---|---|
| `batch_id` | К какой партии относится. |
| `barcode` | Полный ШПИ, например `CC010000359KZ`. |
| `package_type` | Код. |
| `department_id` | Отделение. |
| `range_id` | Диапазон, если код создан из диапазона. |
| `sequence_number` | Числовой номер внутри счетчика/диапазона. |
| `printed` | Был ли PDF скачан как печать. |
| `printed_at` | Когда отмечен printed. |
| `status` | Lifecycle status. |
| `cancelled_at`, `cancelled_by`, `cancellation_reason` | Отмена ШПИ. |
| `used_at`, `used_by`, `usage_notes` | Использование ШПИ. |

### printed_batches

Файл:

```text
backend/app/models/printed_batch.py
```

Для чего:

История скачивания PDF с отметкой “напечатано”.

Важно:

Backend не управляет физическим принтером. Он только:

1. Генерирует PDF.
2. Отмечает barcodes как printed.
3. Создает запись в `printed_batches`.

### audit_logs

Файл:

```text
backend/app/models/audit_log.py
```

Для чего:

Журнал действий: login, создание клиента, создание user, генерация, печать, отмена, approve/reject заявки.

### app_settings

Файл:

```text
backend/app/models/app_setting.py
```

Для чего:

Настройки генерации.

Сейчас используются:

| key | default | Для чего |
|---|---|---|
| `obl_code` | `01` | Первые 2 цифры тела ШПИ. |
| `country_suffix` | `KZ` | Суффикс страны. |

## 5. Как строится ШПИ

Файл:

```text
backend/app/services/barcode_number_service.py
```

Формат:

```text
{package_type}{obl_code}{counter_6_digits}{check_digit}{suffix}
```

Пример:

```text
CC010000359KZ
```

Разбор:

| Часть | Пример | Значение |
|---|---|---|
| `package_type` | `CC` | 2 латинские буквы. |
| `obl_code` | `01` | Берется из `app_settings`, default `01`. |
| `counter_6_digits` | `000035` | Номер из счетчика или диапазона. |
| `check_digit` | `9` | Контрольная цифра. |
| `suffix` | `KZ` | Страна, default `KZ`. |

Правила:

| Поле | Ограничение |
|---|---|
| `package_type` | Ровно 2 uppercase латинские буквы. |
| `quantity` | От 1 до 1000 для генерации партии. |
| `counter_value` | Максимум `999999`. |

Check digit считается по 8 цифрам:

```text
obl_code + counter_6_digits
```

Веса:

```text
8, 6, 4, 2, 3, 5, 9, 7
```

## 6. Главные flow

### Flow A. Login

Endpoint:

```text
POST /api/auth/login
```

Что читает:

```text
users
```

Что пишет:

```text
audit_logs
```

Что возвращает:

```text
JWT access_token
```

После этого frontend вызывает:

```text
GET /api/auth/me
```

### Flow B. Admin создает клиента

Endpoint:

```text
POST /api/clients
```

Роли:

```text
admin
```

Request:

```json
{
  "name": "Client name",
  "contact_person": "Name",
  "contact_phone": "+7...",
  "email": "mail@example.com",
  "notes": "text",
  "is_active": true
}
```

Что пишет:

```text
clients
audit_logs
```

### Flow C. Admin создает client-user

Endpoint:

```text
POST /api/users
```

Роли:

```text
admin
```

Request:

```json
{
  "username": "client1",
  "password": "client123",
  "full_name": "Client User",
  "role": "client",
  "department_id": null,
  "client_id": 10,
  "is_active": true
}
```

Важно:

Если `role = client`, то `client_id` обязателен.

Что пишет:

```text
users
audit_logs
```

### Flow D. Клиент создает заявку на диапазон

Endpoint:

```text
POST /api/range-requests
```

Роли:

```text
admin, operator, client
```

Request:

```json
{
  "purpose": "Нужно для отправок",
  "requested_quantity": 500,
  "department_id": 50,
  "requested_code": "CC",
  "package_type": null,
  "client_id": null,
  "request_type": "issue_range",
  "payload": null,
  "notes": "text"
}
```

Важное правило:

Если заявку создает `client`, backend игнорирует чужой `client_id` и берет `client_id` из JWT user.

Что пишет:

```text
range_requests
audit_logs
```

Стартовый статус:

```text
pending
```

### Flow E. Admin/operator одобряет заявку

Endpoint:

```text
POST /api/range-requests/{request_id}/approve
```

Роли:

```text
admin, operator
```

Request:

```json
{
  "approved_code": "CC",
  "expires_at": "2026-12-31T00:00:00Z",
  "notes": "approved"
}
```

Что происходит:

1. Проверяется, что заявка `pending`.
2. Проверяется `approved_code` в `barcode_code_catalog`.
3. Проверяется, что для кода есть строка в `barcode_counters`.
4. Если catalog status был `available`, он становится `active`.
5. Из `barcode_counters.current_value` режется диапазон.
6. Создается `barcode_ranges`.
7. `barcode_counters.current_value` сдвигается вперед на размер диапазона.
8. `range_requests.status` становится `approved`.
9. Пишется audit.

Что пишет:

```text
barcode_code_catalog
barcode_counters
barcode_ranges
range_requests
audit_logs
```

Пример:

До approve:

```text
barcode_counters.CC.current_value = 1000
requested_quantity = 500
```

После approve:

```text
barcode_ranges.start_number = 1001
barcode_ranges.end_number = 1500
barcode_ranges.current_number = 1001
barcode_counters.CC.current_value = 1500
```

### Flow F. Admin/operator отклоняет заявку

Endpoint:

```text
POST /api/range-requests/{request_id}/reject
```

Роли:

```text
admin, operator
```

Request:

```json
{
  "notes": "reason"
}
```

Что пишет:

```text
range_requests.status = rejected
range_requests.handled_by
range_requests.handled_at
range_requests.decision_notes
audit_logs
```

### Flow G. Клиент или сотрудник отменяет заявку

Endpoint:

```text
POST /api/range-requests/{request_id}/cancel
```

Роли:

```text
admin, operator, client
```

Клиент может отменить только заявку своей организации.

Можно отменить только:

```text
pending
```

Что пишет:

```text
range_requests.status = cancelled
range_requests.handled_by
range_requests.handled_at
audit_logs
```

### Flow H. Генерация ШПИ напрямую, без диапазона

Endpoint:

```text
POST /api/barcodes/numbers
```

Роли:

```text
admin, operator
```

Request:

```json
{
  "package_type": "CC",
  "quantity": 5,
  "department_id": 50,
  "notes": "text"
}
```

Что происходит:

1. Проверяется `package_type`.
2. Проверяется `quantity`.
3. Блокируется строка `barcode_counters` через `with_for_update`.
4. Берутся следующие номера.
5. `barcode_counters.current_value` сдвигается вперед.
6. Создается `generated_batches`.
7. Создаются строки `generated_barcodes`.
8. Пишется audit `barcode_generated`.

Что пишет:

```text
barcode_counters
generated_batches
generated_barcodes
audit_logs
```

Response:

```json
{
  "batch_id": 123,
  "items": ["CC010000001KZ"],
  "count": 1,
  "first_barcode": "CC010000001KZ",
  "last_barcode": "CC010000001KZ"
}
```

### Flow I. Генерация ШПИ из диапазона

Endpoint:

```text
POST /api/ranges/{range_id}/generate
```

Роли:

```text
admin, operator, client
```

Request:

```json
{
  "quantity": 50,
  "notes": "text"
}
```

Важное правило:

Клиент может генерировать только из диапазона своей организации.

Что происходит:

1. Backend помечает просроченные диапазоны как `expired`.
2. Проверяет, что range существует.
3. Проверяет доступ клиента.
4. Проверяет, что range `active`.
5. Проверяет, что `quantity` помещается в остаток.
6. Генерирует ШПИ из `barcode_ranges.current_number`.
7. Сдвигает `barcode_ranges.current_number`.
8. Если дошли до конца, ставит `barcode_ranges.status = exhausted`.
9. Создает `generated_batches` с `source = range`.
10. Создает `generated_barcodes`.
11. Пишет audit.

Что пишет:

```text
barcode_ranges
generated_batches
generated_barcodes
audit_logs
```

Важно:

При генерации из диапазона `barcode_counters` уже не меняется.
Он был сдвинут заранее при approve заявки.

### Flow J. PDF preview

Endpoint:

```text
GET /api/barcodes/batches/{batch_id}/pdf-preview
```

Роли:

```text
admin, operator, client
```

Клиент может смотреть PDF только своих batch.

Что делает:

1. Читает `generated_batches`.
2. Читает `generated_barcodes`.
3. Читает `departments.name`, если есть department_id.
4. Генерирует PDF.
5. Пишет audit `pdf_preview_generated`.

Что не делает:

```text
Не меняет printed.
Не создает printed_batches.
Не меняет status barcode.
```

### Flow K. Скачать PDF и отметить как напечатано

Endpoint:

```text
POST /api/barcodes/batches/{batch_id}/pdf
```

Роли:

```text
admin, operator, client
```

Request:

```json
{
  "printed_by": null,
  "printer_name": "Browser download",
  "notes": "text"
}
```

Что делает:

1. Проверяет доступ к batch.
2. Читает `generated_batches`.
3. Читает все `generated_barcodes` batch-а.
4. Генерирует PDF.
5. Создает запись `printed_batches`.
6. Для каждого barcode ставит:
   - `printed = true`
   - `printed_at = now`
   - `status = printed`, если он еще не `used` и не `cancelled`
7. Пишет audit:
   - `batch_printed` для admin/operator
   - `client_pdf_downloaded` для client

Что пишет:

```text
printed_batches
generated_barcodes
audit_logs
```

Важно:

Backend не печатает на физический принтер.
Он только отдает PDF и фиксирует факт “напечатано”.

### Flow L. Отмена конкретного ШПИ

Endpoint:

```text
POST /api/barcodes/{barcode}/cancel
```

Роли:

```text
admin, operator
```

Request:

```json
{
  "reason": "reason"
}
```

Можно отменить только barcode со статусом:

```text
generated или printed
```

Нельзя отменить:

```text
used
cancelled
```

Что пишет:

```text
generated_barcodes.status = cancelled
generated_barcodes.cancelled_at
generated_barcodes.cancelled_by
generated_barcodes.cancellation_reason
audit_logs
```

### Flow M. Пометить ШПИ использованным

Endpoint:

```text
POST /api/barcodes/{barcode}/mark-used
```

Роли:

```text
admin, operator
```

Request:

```json
{
  "notes": "optional"
}
```

Можно использовать только barcode со статусом:

```text
generated или printed
```

Нельзя использовать:

```text
cancelled
used
```

Что пишет:

```text
generated_barcodes.status = used
generated_barcodes.used_at
generated_barcodes.used_by
generated_barcodes.usage_notes
audit_logs
```

## 7. Endpoint-ы

### Health

| Method | URL | Роли | Что делает |
|---|---|---|---|
| GET | `/api/health` | public | Проверка, что backend жив. |

### Auth

| Method | URL | Роли | Body / Query | Response |
|---|---|---|---|---|
| POST | `/api/auth/login` | public | form-urlencoded `username`, `password` | `Token` |
| GET | `/api/auth/me` | auth | - | `UserRead` |

### Users

Файл:

```text
backend/app/api/routes/users.py
```

Все endpoints только для `admin`.

| Method | URL | Body / Query | Что делает |
|---|---|---|---|
| POST | `/api/users` | `UserCreate` | Создает user, пишет audit. |
| GET | `/api/users?limit=100&offset=0` | query | Список users. |
| GET | `/api/users/{user_id}` | - | Один user. |
| PATCH | `/api/users/{user_id}` | `UserUpdate` | Обновляет user, пишет audit. |

`UserCreate`:

```json
{
  "username": "operator1",
  "password": "operator123",
  "full_name": "Name",
  "role": "operator",
  "department_id": null,
  "client_id": null,
  "is_active": true
}
```

### Clients

Файл:

```text
backend/app/api/routes/clients.py
```

| Method | URL | Роли | Body / Query | Что делает |
|---|---|---|---|---|
| GET | `/api/clients` | admin, operator | `search`, `limit`, `offset`, `is_active` | Список клиентов. |
| POST | `/api/clients` | admin | `ClientCreate` | Создает клиента, пишет audit. |
| GET | `/api/clients/{client_id}` | admin, operator | - | Один клиент. |
| PATCH | `/api/clients/{client_id}` | admin | `ClientUpdate` | Обновляет клиента. |

### Departments

Файл:

```text
backend/app/api/routes/departments.py
```

Любой залогиненный user.

| Method | URL | Body / Query | Что делает |
|---|---|---|---|
| GET | `/api/departments` | `search`, `limit`, `offset` | Плоский список отделений. |
| GET | `/api/departments/tree` | - | Дерево отделений. |

### Barcode codes

Файл:

```text
backend/app/api/routes/barcode_codes.py
```

Роли:

```text
admin, operator
```

| Method | URL | Body / Query | Что делает |
|---|---|---|---|
| GET | `/api/barcode-codes` | `limit`, `offset`, `status` | Список кодов. |
| GET | `/api/barcode-codes/{code}` | - | Один код. |

### Range requests

Файл:

```text
backend/app/api/routes/range_requests.py
```

| Method | URL | Роли | Body / Query | Что делает |
|---|---|---|---|---|
| POST | `/api/range-requests` | admin, operator, client | `RangeRequestCreate` | Создает заявку. |
| GET | `/api/range-requests` | admin, operator, client | filters | Список заявок. Client видит только свою организацию. |
| GET | `/api/range-requests/{request_id}` | admin, operator, client | - | Одна заявка. |
| POST | `/api/range-requests/{request_id}/approve` | admin, operator | `RangeRequestDecision` | Одобряет заявку и создает диапазон. |
| POST | `/api/range-requests/{request_id}/reject` | admin, operator | `RangeRequestDecision` | Отклоняет заявку. |
| POST | `/api/range-requests/{request_id}/cancel` | admin, operator, client | `RangeRequestDecision` | Отменяет pending-заявку. |

Filters для list:

```text
limit
offset
status
package_type
client_id
department_id
```

### Ranges

Файл:

```text
backend/app/api/routes/ranges.py
```

| Method | URL | Роли | Body / Query | Что делает |
|---|---|---|---|---|
| GET | `/api/ranges/my` | admin, operator, client | `limit`, `offset`, `status` | Диапазоны текущего client_id. Если client_id нет, вернет empty list. |
| GET | `/api/ranges` | admin, operator | filters | Все диапазоны. |
| POST | `/api/ranges/{range_id}/generate` | admin, operator, client | `RangeGenerateRequest` | Генерирует ШПИ из диапазона. |
| GET | `/api/ranges/{range_id}/remaining` | admin, operator, client | - | Остаток диапазона. |
| POST | `/api/ranges/{range_id}/cancel` | admin, operator | `RangeCancelRequest` | Отменяет диапазон. |
| POST | `/api/ranges/{range_id}/renew` | admin, operator | `RangeRenewRequest` | Продлевает диапазон. |
| GET | `/api/ranges/{range_id}/batches` | admin, operator | `limit`, `offset` | Партии, созданные из диапазона. |
| GET | `/api/ranges/{range_id}` | admin, operator, client | - | Один диапазон. Client только свой. |

Filters для `/api/ranges`:

```text
limit
offset
package_type
status
client_id
department_id
```

### Barcodes

Файл:

```text
backend/app/api/routes/barcodes.py
```

| Method | URL | Роли | Body / Query | Что делает |
|---|---|---|---|---|
| POST | `/api/barcodes/numbers` | admin, operator | `BarcodeNumberRequest` | Генерация без диапазона. |
| GET | `/api/barcodes/lifecycle` | admin, operator | filters | Список barcode по lifecycle. |
| GET | `/api/barcodes/{barcode}/detail` | admin, operator, client | - | Детали barcode. |
| POST | `/api/barcodes/{barcode}/cancel` | admin, operator | `BarcodeCancelRequest` | Отменяет barcode. |
| POST | `/api/barcodes/{barcode}/mark-used` | admin, operator | `BarcodeMarkUsedRequest` | Помечает barcode использованным. |
| GET | `/api/barcodes/history/batches` | admin, operator | filters | История batch. |
| GET | `/api/barcodes/history/batches/{batch_id}` | admin, operator | - | Batch detail. |
| GET | `/api/barcodes/history/search?barcode=...` | admin, operator | `barcode` | Поиск barcode. |
| GET | `/api/barcodes/my-batches` | admin, operator, client | `limit`, `offset` | Batch текущего client_id. |
| GET | `/api/barcodes/my-batches/{batch_id}` | admin, operator, client | - | Batch detail клиента. |
| GET | `/api/barcodes/my-print-history` | admin, operator, client | `limit`, `offset` | Print history клиента. |
| GET | `/api/barcodes/batches/{batch_id}/pdf-preview` | admin, operator, client | - | PDF preview без отметки printed. |
| POST | `/api/barcodes/batches/{batch_id}/pdf` | admin, operator, client | `PrintBatchRequest` | PDF download + mark printed. |
| GET | `/api/barcodes/print-history` | admin, operator | filters | Общая история печати. |

Filters для lifecycle:

```text
status
package_type
department_id
printed
limit
offset
```

Filters для history batches:

```text
limit
offset
package_type
department_id
```

Filters для print-history:

```text
limit
offset
department_id
generated_batch_id
```

### Audit logs

Файл:

```text
backend/app/api/routes/audit.py
```

Роли:

```text
admin
```

| Method | URL | Body / Query | Что делает |
|---|---|---|---|
| GET | `/api/audit-logs` | `limit`, `offset`, `action`, `username` | Список audit logs. |

## 8. Статусы

### range_requests.status

| Статус | Что значит |
|---|---|
| `pending` | Заявка создана, решения еще нет. |
| `approved` | Заявка одобрена, диапазон создан. |
| `rejected` | Заявка отклонена. |
| `cancelled` | Заявка отменена. |

### barcode_ranges.status

| Статус | Что значит |
|---|---|
| `active` | Можно генерировать. |
| `exhausted` | Все номера диапазона использованы. |
| `expired` | Истек срок действия. |
| `cancelled` | Диапазон отменен. |

### generated_barcodes.status

| Статус | Что значит |
|---|---|
| `generated` | Код создан, PDF еще не отмечал его printed. |
| `printed` | PDF скачан через print endpoint, код отмечен printed. |
| `used` | Код помечен использованным. |
| `cancelled` | Код отменен. |

### barcode_code_catalog.status

| Статус | Что значит |
|---|---|
| `available` | Можно выдать клиенту. |
| `active` | Уже используется, но тоже можно выдавать. |
| `reserved` | Зарезервирован, нельзя выдавать. |
| `blocked` | Заблокирован, нельзя выдавать. |
| `deprecated` | Устарел, нельзя выдавать. |

## 9. Где искать логику по задаче

| Если нужно понять | Смотреть |
|---|---|
| Login/JWT/roles | `services/auth_service.py`, `core/security.py`, `api/routes/auth.py` |
| Создание users | `api/routes/users.py`, `services/auth_service.py` |
| Clients | `api/routes/clients.py`, `services/client_service.py` |
| Departments tree | `api/routes/departments.py`, `services/department_service.py` |
| Справочник кодов | `api/routes/barcode_codes.py`, `services/barcode_code_service.py` |
| Заявки на диапазоны | `api/routes/range_requests.py`, `services/range_request_service.py` |
| Диапазоны | `api/routes/ranges.py`, `services/barcode_range_service.py` |
| Генерация из диапазона | `services/range_generation_service.py` |
| Генерация без диапазона | `services/barcode_number_service.py` |
| История batch/search | `services/barcode_history_service.py` |
| PDF | `services/pdf_label_service.py` |
| Print history | `services/print_tracking_service.py` |
| Cancel/used barcode | `services/barcode_lifecycle_service.py` |
| Audit | `services/audit_service.py`, `api/routes/audit.py` |

## 10. Что frontend должен помнить

1. Login отправлять как form-urlencoded, не JSON.
2. Все protected requests отправлять с header:

```text
Authorization: Bearer <token>
```

3. Client нельзя отправлять на `/generate`, ему нужен `/my-ranges`.
4. Client видит только данные своего `client_id`.
5. PDF preview не меняет `printed`.
6. `POST /api/barcodes/batches/{batch_id}/pdf` меняет `printed` и создает `printed_batches`.
7. Backend не печатает физически. Он только генерирует PDF.
8. Настоящие barcode-номера считает только backend.
9. Frontend не должен считать check digit.
10. При `401` frontend должен делать logout.

## 11. Самые важные цепочки таблиц

### Заявка -> диапазон -> генерация -> печать

```text
range_requests
  -> barcode_ranges
    -> generated_batches
      -> generated_barcodes
        -> printed_batches
```

### Client ownership

```text
clients.id
  -> users.client_id
  -> range_requests.client_id
  -> barcode_ranges.issued_to_client_id
  -> generated_batches.range_id
  -> generated_barcodes.range_id
```

Client-доступ к batch проверяется через:

```text
generated_batches.range_id -> barcode_ranges.issued_to_client_id
```

### Direct generation без client ownership

```text
barcode_counters
  -> generated_batches(source = api, range_id = null)
  -> generated_barcodes(range_id = null)
```

Этот flow доступен только admin/operator.

## 12. Быстрая проверка backend вручную

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Me:

```bash
curl http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

Departments tree:

```bash
curl http://127.0.0.1:8000/api/departments/tree \
  -H "Authorization: Bearer <token>"
```

Generate direct:

```bash
curl -X POST http://127.0.0.1:8000/api/barcodes/numbers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"package_type\":\"CC\",\"quantity\":5,\"department_id\":50,\"notes\":\"test\"}"
```

PDF preview:

```bash
curl http://127.0.0.1:8000/api/barcodes/batches/1/pdf-preview \
  -H "Authorization: Bearer <token>" \
  --output preview.pdf
```

PDF + mark printed:

```bash
curl -X POST http://127.0.0.1:8000/api/barcodes/batches/1/pdf \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"printer_name\":\"Browser download\",\"notes\":\"test\"}" \
  --output labels.pdf
```

## 13. Главная мысль

Backend построен вокруг одной цепочки:

```text
client/user создает заявку
admin/operator одобряет
backend создает диапазон
client/operator генерирует ШПИ из диапазона
backend создает batch и barcodes
PDF endpoint отмечает barcodes как printed
operator может отменить или пометить barcode used
audit_logs фиксирует действия
```

Если непонятно, где искать баг:

1. Сначала найди endpoint в `api/routes`.
2. Посмотри request/response в `schemas`.
3. Перейди в service, который вызывает endpoint.
4. Проверь model/table, которые service меняет.
5. Проверь audit action, если действие должно логироваться.

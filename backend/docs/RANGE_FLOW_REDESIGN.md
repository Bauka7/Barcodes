# Редизайн потока выдачи диапазонов ШПИ (ветка `backend`)

Документация по всем изменениям бэкенда. Описывает **что добавили/изменили** и **зачем**.
Все изменения сделаны поверх коммита `Implement frontend MVP` и на момент написания не закоммичены.

---

## 1. Назначение

Раньше клиент сам генерировал ШПИ, указывая 2-буквенный код. Это неправильно: коды —
ограниченный общий ресурс, и раздавать их «самообслуживанием» нельзя.

Новый поток разводит ответственность по трём ролям:

- **Клиент (организация/почтомат)** — *описывает потребность* (что и сколько), не выбирает код.
- **Модератор (operator/admin)** — рассматривает заявку, *назначает код* из справочника и
  *выдаёт диапазон*.
- **Админ** — может всё, плюс заводит организации и пользователей, ведёт справочник кодов.

Идеальный сценарий:

```
Клиент: заявка (назначение + количество + отделение)
   → Модератор: одобрение с кодом → система режет диапазон вперёд по счётчику
   → Клиент: видит свой диапазон → генерирует ШПИ → печатает PDF (с названием отдела)
```

---

## 2. Модель владения

Опора всего потока — **организация** (таблица `clients`). Одна организация → много
пользователей. Всё «своё» (заявки, диапазоны, партии, PDF) определяется по `client_id`
пользователя, а не по конкретному автору.

- Пользователь с ролью `client` **обязан** иметь `client_id`.
- Диапазон выдаётся организации (`barcode_ranges.issued_to_client_id`).
- Партия принадлежит организации через связь `партия → диапазон → организация`.

---

## 3. Изменения схемы БД

### 3.1 `users.client_id` (миграция `0009`)
| Колонка | Тип | Назначение |
|---|---|---|
| `client_id` | FK → `clients.id`, `SET NULL`, индекс, nullable | Привязка пользователя к организации |

**Зачем:** ввести владение «организация → пользователи». `SET NULL` — удаление организации
не каскадит на пользователей. `department_id` у пользователя оставлен как был (это отделение
КазПочты — отдельная сущность, не заменяется организацией).

Миграция дополнительно **бэкафиллит** существующих client-пользователей: если есть клиенты
без организации, создаётся `clients(name='Демо-организация')` и они к ней привязываются.

### 3.2 Справочник кодов `barcode_code_catalog` (миграция `0010`)
| Колонка | Тип | Назначение |
|---|---|---|
| `code` | String(20), unique, index | 2-буквенный код направления |
| `name` | String(255), nullable | Человекочитаемое название |
| `category` | String(100), nullable | Категория |
| `status` | String(50), default `available`, index | available / active / reserved / blocked / deprecated |
| `owner` | String(255), nullable | Назначение/владелец направления |
| `notes` | Text, nullable | Заметки |

CHECK-ограничение на допустимые статусы.

**Зачем:** дать кодам управляемый «жизненный цикл» и единый источник правды для модератора.
`available` — код свободен; `active` — уже выдавался; `blocked/deprecated` — выдавать нельзя.

### 3.3 Поля заявки `range_requests` (миграция `0011`)
| Колонка | Изменение | Назначение |
|---|---|---|
| `package_type` | стал **nullable** | На этапе заявки кода может не быть |
| `purpose` | новый, Text | Описание потребности (тип товара/назначение) |
| `requested_code` | новый, String(20) | Желаемый клиентом код (необязательное пожелание) |
| `approved_code` | новый, String(20) | Код, назначенный модератором при одобрении |
| `decision_notes` | новый, Text | Комментарий модератора к решению |

**Зачем:** заявка превращается из «дай код XX» в «опиши потребность». Код назначает модератор
(`approved_code`); клиент может лишь предложить (`requested_code`).

> Таблицы `barcode_ranges`, `barcode_counters`, `generated_batches/barcodes`, `printed_batches`
> **не менялись** — нужная инфраструктура (`issued_to_client_id`, `issued_to_department_id`,
> `request_id`, счётчик) там уже была.

---

## 4. API: новые эндпоинты

| Метод | Путь | Роли | Назначение |
|---|---|---|---|
| GET | `/api/barcode-codes` | admin, operator | Список кодов справочника (фильтр `status`) |
| GET | `/api/barcode-codes/{code}` | admin, operator | Одна запись справочника |
| GET | `/api/ranges/my` | client (+staff) | Диапазоны моей организации |
| GET | `/api/barcodes/my-batches` | client (+staff) | Партии моей организации |
| GET | `/api/barcodes/my-batches/{id}` | client (+staff) | Деталь своей партии (иначе 404) |
| GET | `/api/barcodes/my-print-history` | client (+staff) | История печати моей организации |

Для staff `my-*`/`ranges/my` возвращают `[]` (у них нет `client_id`) — клиентские ручки,
сотрудники пользуются полными списками.

**Зачем:** дать клиенту видеть и использовать ровно «своё», без доступа к чужим данным.

---

## 5. API: изменённые эндпоинты

| Метод | Путь | Было → Стало | Зачем |
|---|---|---|---|
| GET | `/api/auth/me`, `/api/users*` | +поле `client_id` | Фронт знает организацию пользователя |
| POST | `/api/barcodes/numbers` | client убран → **только staff** | Прямую генерацию клиенту запретили |
| POST | `/api/range-requests` | требовал `package_type` → требует `purpose`+`department_id`; код опционален; клиенту `client_id` ставит сервер | Заявка-потребность; клиент не подставит чужой `client_id` |
| GET | `/api/range-requests` | клиент видел свои (по автору) → видит **по организации** | Заявки общие для организации |
| POST | `/api/range-requests/{id}/approve` | принимал только `notes` → принимает `approved_code` | Модератор назначает код; диапазон режется из него |
| POST | `/api/range-requests/{id}/cancel` | staff → **+client (свою pending)** | Клиент может отозвать свою заявку |
| POST | `/api/ranges/{id}/generate` | staff → **+client (свой диапазон)** | Клиент генерирует из выданного диапазона |
| GET | `/api/ranges/{id}`, `/remaining` | staff → **+client (свой)** | Клиенту нужен остаток перед генерацией |
| GET | `/api/barcodes/batches/{id}/pdf-preview` | без проверки → **client только свои** | Закрыли утечку чужих PDF |
| POST | `/api/barcodes/batches/{id}/pdf` | staff → **+client (свои)** | Клиент печатает свои наклейки |

`/api/ranges` (список) и `/api/ranges/{id}/batches` остались staff-only.

---

## 6. Бизнес-правила (логика)

### 6.1 Правило «client → client_id»
`create_user`/`update_user`: пользователь с ролью `client` обязан иметь `client_id`,
иначе `ValueError` (HTTP 400). **Зачем:** без организации client-аккаунт ничего не «увидит».

### 6.2 Создание заявки
- `purpose` и `department_id` — обязательны; `requested_quantity` валидируется.
- `package_type`/`requested_code` валидируются только если переданы.
- Для роли `client` `client_id` **принудительно** берётся из аккаунта (нельзя подставить чужой);
  staff указывает `client_id` явно.
- `department_id` обязателен, потому что **название отдела печатается на наклейке**.

### 6.3 Одобрение (назначение кода + резерв)
1. `code = approved_code` (или `package_type` заявки для legacy); если нет — ошибка.
2. `ensure_code_allocatable(code)`: код есть в справочнике, статус `available/active`,
   под него есть счётчик; при первой выдаче `available → active`.
3. `code` фиксируется на заявке (`package_type`, `approved_code`).
4. `create_barcode_range_from_request` блокирует счётчик `code` (`FOR UPDATE`), режет блок
   **вперёд**: `start = counter+1`, `end = counter+quantity`, двигает счётчик; создаёт
   `barcode_range(status=active, issued_to_client_id=заявка.client_id,
   issued_to_department_id=заявка.department_id, request_id=...)`.

**Зачем:** аллокация forward-only (без наложений), отдел из заявки уходит в диапазон → в
партию → на наклейку.

### 6.4 Владение при генерации/PDF
- Генерация из диапазона: клиент — только `issued_to_client_id == user.client_id`, иначе 403.
- PDF preview/print: клиент — только партии своей организации (связь партия→диапазон→организация).

### 6.5 Forward-only аллокация
Диапазоны режутся только «вперёд» по `barcode_counters`. Переиспользование отменённых/истёкших
диапазонов **намеренно отложено** (см. §9).

---

## 7. Аудит

Добавлены/уточнены действия:
- `range_request_approved` — теперь с `approved_code` в деталях.
- `range_request_cancelled_by_client` — когда отменяет клиент (иначе `range_request_cancelled`).
- `client_range_generated` — клиент сгенерировал из своего диапазона.
- `client_pdf_downloaded` — клиент скачал PDF (вместо `batch_printed`).

**Зачем:** в журнале видно, что именно делал клиент против действий сотрудников.

---

## 8. Сид данных

`seed.py` → `seed_code_catalog()`: для каждого кода из `DEFAULT_PACKAGE_TYPES` создаёт запись
в `barcode_code_catalog` (status `available`), если её ещё нет. Вызывается из `seed_database()`.

**Зачем:** справочник наполняется теми же 30 кодами, что и счётчики (синхрон каталог ↔ счётчики),
чтобы любой одобряемый код имел счётчик для генерации.

---

## 9. Намеренно отложено

- **Переиспользование** отменённых/истёкших диапазонов (reuse) — аллокация пока только forward.
- Проверка наложений и ручной ввод `start–end` — не нужны при forward-only.
- Полноценный CRUD справочника кодов для админа (сейчас только чтение `GET`).

---

## 10. Файлы изменений

**Новые (7):**
- `app/models/barcode_code_catalog.py`
- `app/schemas/barcode_code.py`
- `app/services/barcode_code_service.py`
- `app/api/routes/barcode_codes.py`
- `alembic/versions/0009_add_client_id_to_users.py`
- `alembic/versions/0010_add_barcode_code_catalog.py`
- `alembic/versions/0011_range_request_need_fields.py`

**Изменённые (16):** `models/user.py`, `models/range_request.py`, `models/__init__.py`,
`schemas/user.py`, `schemas/range_request.py`, `schemas/__init__.py`, `services/auth_service.py`,
`services/range_request_service.py`, `services/barcode_history_service.py`,
`services/print_tracking_service.py`, `api/routes/auth.py`, `api/routes/barcodes.py`,
`api/routes/range_requests.py`, `api/routes/ranges.py`, `api/router.py`, `db/seed.py`.

---

## 11. Как применить

Код вшивается в Docker-образ при сборке, поэтому миграции `0009–0011` и новые ручки
активируются после пересборки бэка:

```
docker compose up -d --build backend
```

Команда контейнера уже выполняет `alembic upgrade head` и сиды на старте.

Цепочка миграций: `0008 → 0009 → 0010 → 0011`.

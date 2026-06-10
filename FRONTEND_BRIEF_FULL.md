# QazPostWeb — Frontend Brief (полный, все роли)

Цель: собрать веб-фронт на React для backend QazPostWeb. Бэкенд готов и требует
авторизацию (JWT). Сделать ВСЕ страницы, которые поддержаны бэком, с навигацией
и доступом по трём ролям: admin, operator, client.

Визуальный референс: design/design-reference.html (открыть в браузере) — оттуда
берём цвета, сайдбар, плотность, бейджи, оформление. Архитектуру и контракт берём
из этого файла. Точные типы запросов/ответов — из /openapi.json.

Этот файл — единственный источник правды. Старые FRONTEND_BRIEF.md и
FRONTEND_MVP_BRIEF.md можно удалить.

---

## 1. Доступ к бэку
- Base API в env: VITE_API_BASE (напр. http://127.0.0.1:8000 локально или адрес
  в общей сети). Все маршруты под /api.
- Swagger: <base>/docs. Тестовый вход: admin / admin123.
- /openapi.json отдаётся без токена и без БД (движок ленивый) — типы генерим всегда.

## 2. Стек и структура
- Vite + React + TypeScript, React Router, TanStack Query, Tailwind,
  react-i18next (ru/kz), openapi-typescript.

  src/
    api/
      client.ts        fetch-обёртка + интерсептор Authorization: Bearer + 401/403
      generated.ts     типы из openapi-typescript (НЕ редактировать)
      <feature>.ts     auth, barcodes, ranges, rangeRequests, clients, users,
                       audit, departments
    auth/
      AuthContext.tsx  токен + профиль (role) + login/logout
      ProtectedRoute.tsx  гард по токену и роли (props: roles[])
    components/        AppShell, Sidebar, BarcodeView, DataTable, StatusBadge,
                       RoleBadge, DepartmentTree, Pagination, ConfirmDialog
    pages/             см. раздел 6
    i18n/              ru.json, kz.json, index.ts
    lib/               departmentName.ts (id -> name через дерево)

## 3. Авторизация (КРИТИЧНО)
1. Login — POST /api/auth/login, тело form-urlencoded (НЕ JSON), поля username,
   password. Ответ { access_token, token_type }. 401 — неверно.
2. Хранить токен, добавлять Authorization: Bearer <token> на КАЖДЫЙ /api запрос
   (интерсептор в client.ts).
3. GET /api/auth/me -> { id, username, full_name, role, department_id, is_active }.
   role in admin|operator|client. По роли — навигация и гарды.
4. Logout = удалить токен, уйти на /login.
5. Глобально: 401 -> почистить токен, на /login; 403 -> "нет доступа".
6. Поля, которые сервер задаёт из токена — НЕ слать с фронта: generated_by
   (генерация), printed_by (печать).

## 4. Дизайн-токены (как в design-reference.html)
- accent #1B4FA0, accent-dark #143C7A, tint #E8EEF8, success #1D9E75,
  danger #E24B4A; радиусы 8/12; sans + mono (для ШПИ); компактная плотность;
  светлая/тёмная тема с переключателем; штрихкод всегда чёрный на белом.
- Сайдбар с пунктами по роли, переключатель РУ/ҚАЗ, бейдж роли и "Выйти" внизу.

## 5. Каталог эндпоинтов и роли (всё под /api)
Роли в скобках — кому разрешено (иначе 403).

Auth/Health
- GET /health — открыто
- POST /auth/login (форма) — открыто; GET /auth/me — любой вошедший

Barcodes
- POST /barcodes/numbers (admin, operator, client) — генерация партии.
  Тело { package_type, quantity, department_id?, notes? } (generated_by НЕ слать).
  Ответ { batch_id, items[], count, first_barcode, last_barcode }.
- GET /barcodes/lifecycle (admin, operator) — список ШПИ; query status,
  package_type, department_id, printed, limit, offset -> { items, count }
- GET /barcodes/{barcode}/detail (admin, operator, client) — деталь ШПИ
  (вкл. department с именем и range)
- POST /barcodes/{barcode}/cancel (admin, operator) — тело { reason }
- POST /barcodes/{barcode}/mark-used (admin, operator) — тело { notes? }
- GET /barcodes/history/batches (admin, operator) — query limit/offset/
  package_type/department_id
- GET /barcodes/history/batches/{batch_id} (admin, operator)
- GET /barcodes/history/search?barcode=... (admin, operator)
- GET /barcodes/batches/{batch_id}/pdf-preview (admin, operator, client) — PDF blob
- POST /barcodes/batches/{batch_id}/pdf (admin, operator) — тело
  { printed_by?, printer_name?, notes? } -> PDF blob, помечает printed
- GET /barcodes/print-history (admin, operator)

Departments (без ролевого ограничения; токен слать всё равно)
- GET /departments (query search/limit/offset) · GET /departments/tree

Ranges (admin, operator)
- GET /ranges · GET /ranges/{id} · GET /ranges/{id}/remaining
- GET /ranges/{id}/batches · POST /ranges/{id}/generate (тело { quantity, notes? })

Range requests
- POST /range-requests (admin, operator, client) — { client_id?, department_id?,
  package_type, requested_quantity, request_type, notes? }
- GET /range-requests · GET /range-requests/{id} (admin, operator, client)
- POST /range-requests/{id}/approve · /reject · /cancel (admin, operator)

Clients
- GET /clients · GET /clients/{id} (admin, operator)
- POST /clients · PATCH /clients/{id} (admin)

Users (admin)
- POST /users · GET /users · GET /users/{id} · PATCH /users/{id}

Audit (admin)
- GET /audit-logs

## 6. Страницы и доступ по ролям
1. Login — все — auth/login, auth/me
2. Генерация ШПИ — admin, operator, client — barcodes/numbers; после успеха
   предпросмотр PDF партии (всем), кнопка "Печать" (admin/operator)
3. Журнал партий + деталь — admin, operator — history/batches, history/batches/{id}
4. Поиск ШПИ — admin, operator — history/search
5. Жизненный цикл ШПИ — admin, operator — lifecycle (фильтры status/printed/
   package_type/department); действия "Отменить" (/cancel), "Использован"
   (/mark-used)
6. Деталь ШПИ — admin, operator, client — {barcode}/detail (для client только
   просмотр; cancel/mark-used скрыть)
7. Печать — preview всем (вкл. client для своей партии), print + история —
   admin, operator — pdf-preview, pdf, print-history
8. Отделения (дерево) — все — departments/tree, departments
9. Диапазоны — admin, operator — ranges, ranges/{id}, /remaining, /batches, /generate
10. Заявки на диапазон — создание/список/деталь всем (client видит свои);
    approve/reject — admin, operator — range-requests (+ /approve /reject /cancel)
11. Клиенты — список/деталь admin+operator; создание/редактирование admin — clients
12. Пользователи — admin — users (создать/список/изменить роль/активность)
13. Журнал аудита — admin — audit-logs
14. Настройки/счётчики — СТАБ (эндпоинтов нет) — заглушка без вызовов API

Навигация по ролям (выверено по бэку):
- admin: Генерация, Журнал, Поиск, Жизненный цикл, Печать, Отделения, Диапазоны,
  Заявки, Клиенты, Пользователи, Аудит, (Настройки-стаб)
- operator: Генерация, Журнал, Поиск, Жизненный цикл, Печать, Отделения,
  Диапазоны, Заявки, Клиенты (просмотр)
- client: Генерация, Мои заявки на диапазон, Деталь ШПИ / предпросмотр PDF своей
  партии. У client НЕТ журнала, поиска, жизненного цикла, печати (POST), истории
  печати, диапазонов, клиентов, пользователей, аудита — там 403, пункты не
  показывать.

## 7. Сквозные правила
- department_id, не имя. Списки (batches, lifecycle, search, ranges, print-history)
  возвращают department_id (число) без имени. Загрузить дерево один раз, построить
  map id->name (lib/departmentName.ts), резолвить в таблицах. Исключение:
  /{barcode}/detail уже отдаёт department с именем.
- PDF — blob. pdf-preview и pdf возвращают application/pdf. Качать/открывать как
  blob, не парсить как JSON.
- lifecycle статус-фильтр идёт query-параметром status (на бэке alias).
- ШПИ-статусы: status у баркода (generated/cancelled/used...) плюс printed.
  Показывать чипами (StatusBadge).
- Типы ответов брать ТОЛЬКО из generated.ts (openapi). Не писать руками.
- Виды пакетов и отделы — с бэка, не хардкодить.

## 8. Конфиги
vite.config.ts прокси:
  server: { proxy: { "/api": process.env.VITE_API_BASE ?? "http://127.0.0.1:8000" } }
Генерация клиента:
  npm i -D openapi-typescript
  npx openapi-typescript "$VITE_API_BASE/openapi.json" -o src/api/generated.ts

## 9. Порядок работы (по одному шагу, показывать результат)
1. Каркас (Vite+TS+Tailwind+Router+i18n+Query) + токены + AppShell + Sidebar
   (фильтр по роли) + переключатель языка + бейдж роли + "Выйти".
2. AuthContext + client.ts (Bearer + 401/403) + ProtectedRoute(roles).
3. LoginPage (форма!) -> /me -> роль.
4. departmentName-map (дерево) + DepartmentTree, DataTable, StatusBadge,
   BarcodeView, Pagination.
5. Генерация -> предпросмотр PDF.
6. Журнал + деталь партии.
7. Поиск + Деталь ШПИ.
8. Жизненный цикл (фильтры + cancel + mark-used).
9. Печать (preview + print + история).
10. Диапазоны + Заявки на диапазон (approve/reject для admin/operator).
11. Клиенты.
12. Пользователи + Аудит (admin).
13. Настройки — стаб.
Каждую страницу гейтить ProtectedRoute по ролям из раздела 6.

# Домовой — контекст для Claude

## Что это

Self-hosted граф-система управления жизнью семьи. Заменяет десятки приложений одной моделью данных: инвентарь, задачи, медицина, IT-инфраструктура, обучение, AI-чаты, плейбуки, документы.

Полная схема данных: `docs/database.md` (~9500 строк).
Сравнение с конкурентами: `docs/comparison.md`.

## Ключевые архитектурные решения

**Граф-модель:** одна таблица `thing` (schemaless), 25 типизированных рёбер. Никаких отдельных таблиц под домены. Новый домен = новые `kind`-значения у `thing`, не новые таблицы.

**Воркеры — конкурирующие потребители:** атомарный захват задачи через `UPDATE ... WHERE status = "ожидание" AND locked_by = NONE`. Язык воркера не важен — TS, Python, Go подключаются к одной очереди. Фильтрация по `kind` + `subtype`.

**LIVE SELECT вместо polling** — воркеры держат WebSocket к SurrealDB, получают задачи мгновенно. Исключение: `worker-scheduler` — polling раз в минуту (сам создаёт задачи по cron).

**MinIO как primary storage** — файлы хранятся в MinIO (S3 API), в SurrealDB только метаданные (`kind: файл`) + чанки с embeddings. Локальный бэкенд только для dev.

**Embeddings в SurrealDB** — MTREE-индекс, измерение 1024 (BGE-M3). Нет отдельного Qdrant/Weaviate. Гибридный поиск: BM25 + vector → RRF → BGE-Reranker.

**Мультиязычность** — поля `_lang` + `_i18n` (embedded JSON) на каждом `thing`. Без отдельных узлов для локалей — переводы путешествуют с узлом при федерации.

**Vision через Ollama** — subtype `vision-local` (qwen2-vl) или `vision-api` (GPT-4o). Тот же паттерн datasource что у LLM и STT.

## Стек

| Слой | Технология |
|------|-----------|
| БД | SurrealDB (RocksDB в prod, memory в тестах) |
| Web | Next.js 15, TypeScript, Tailwind, shadcn/ui, TanStack Query |
| TS-воркеры | Node.js 22 — scheduler, playbook, bot |
| Python-воркеры | Python 3.12 — AI (BGE-M3, Reranker, Whisper), Files (pypdf, tesseract) |
| Storage | MinIO (S3-совместимый) |
| LLM/Embed | Ollama на отдельном GPU-сервере (RTX 3090 24GB) |
| LLM модель | Qwen2.5 32B Q4_K_M |
| Embed модель | BGE-M3 (1024d, multilingual, русский) |
| Reranker | BGE-Reranker-v2-m3 |
| STT | faster-whisper large-v3 |

## Структура проекта

```
domovoy/
├── docker-compose.yml       — dev
├── docker-compose.prod.yml  — prod overrides
├── docker-compose.test.yml  — тесты (SurrealDB memory + MinIO tmpfs)
├── Makefile                 — make up/down/test/deploy/seed/shell-db
├── .env / .env.example
├── web/                     — Next.js (ещё не инициализирован)
├── worker-scheduler/        — TS: cron + counter-триггеры
├── worker-playbook/         — TS: DAG-исполнение плейбуков, HTTP-интеграции
├── worker-bot/              — TS: Telegram, голосовой шлюз
├── worker-ai/               — Python: embeddings, reranker, Whisper, vision
├── worker-files/            — Python: chunking, OCR, thumbnails
├── scripts/
│   └── seed.surql           — тестовый датасет (ещё не написан)
└── docs/
    ├── database.md          — полная схема (~9500 строк)
    └── comparison.md        — сравнение с конкурентами
```

## Текущий статус

- [x] Полная схема данных в `docs/database.md`
- [x] Docker Compose: dev + prod + test
- [x] Makefile с командами
- [ ] `scripts/seed.surql` — тестовый датасет
- [ ] `web/` — инициализировать Next.js проект
- [ ] `worker-scheduler/` — минимальный воркер
- [ ] DEFINE-схема в SurrealDB (из database.md выжать в .surql файл)
- [ ] UI-спайки (спайк A: thing list + detail, спайк B: граф-визуализация)

## Тестовый датасет (запланирован)

~20 узлов: 3 человека (Папа/Мама/Сын), 2 места (Квартира/Гараж), мотоцикл BMW с одометром, ноутбук одолженный сыну, 4 задачи разных статусов с зависимостями, шаблон ТО (counter-based), шаблон платежа (cron), документ ОСАГО, сервер Proxmox.

## Команды

```bash
make infra          # поднять только SurrealDB + MinIO (для локальной разработки)
make up             # поднять всё
make test           # все тесты (TS + Python)
make test-ts        # только TS тесты
make test-e2e       # Playwright E2E
make test-py        # все Python тесты
make shell-db       # SurrealQL REPL
make seed           # залить тестовый датасет
make deploy         # деплой на home-server через SSH
```

## Важные детали

- `.env` в `.gitignore`, не коммитить
- Тесты используют SurrealDB `memory` backend — данные не сохраняются между прогонами
- GPU-сервер (Ollama) внешний, в docker-compose не входит, адрес в `OLLAMA_ENDPOINT`
- Если нужен Go-воркер для конкретного `subtype` — добавить новый сервис в compose, тот же паттерн захвата задачи
- Граф-визуализация в UI — библиотека ещё не выбрана (кандидат: React Flow)

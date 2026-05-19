# Домовой — состояние сессии

_Обновлено: 2026-05-19_

## Что сделано в этой сессии

### Surrealist GUI (self-hosted)

Добавлен Surrealist как Docker-контейнер для отладки SurrealDB через браузер.

**Файлы:**
- `docker/surrealist/Dockerfile` — multi-stage build: `oven/bun:1-alpine` → `nginx:1.27-alpine`
- `docker/surrealist/nginx.conf` — SPA nginx, gzip_static + gunzip on
- `docker/surrealist/instance.json.tmpl` — шаблон pre-configured подключения
- `docker/surrealist/instance.json` — генерируется из .env (gitignored)

**Команды:**
```bash
make surrealist          # генерирует instance.json из .env, поднимает контейнер
make surrealist-update   # pull новой версии + restart
```

**Доступ:** http://localhost:8080

**Ключевые детали:**
- Официальный образ `surrealdb/surrealist:3.8.5` с Docker Hub НЕ использует DockerAdapter — собран без `VITE_SURREALIST_DOCKER=true`, поэтому не читает `instance.json`
- Наш кастомный build из исходников с `VITE_SURREALIST_DOCKER=true` ДОЛЖЕН активировать DockerAdapter
- DockerAdapter читает `/instance.json` при старте и pre-configures подключение

**Нерешённая проблема:**
- DockerAdapter в нашем бандле (`surrealist-CGN5e1pD.js.gz`) есть (подтверждено по содержимому), но при открытии http://localhost:8080 Surrealist всё равно показывает "Create connections" — значит либо DockerAdapter не активирован (`VITE_SURREALIST_DOCKER` не прокидывается в Vite), либо fetch `/instance.json` не срабатывает
- `docker exec domovoy-surrealist-1 sh -c 'zcat ... | grep -oF "instance.json"'` находит только одно вхождение в changelog, не в runtime-коде fetch
- Нужно: либо проверить через DevTools (Network tab) что происходит при загрузке http://localhost:8080, либо пересобрать с `--no-cache` и проверить наличие `"/instance.json"` в бандле

**Следующий шаг по Surrealist:**
1. Открыть http://localhost:8080 в DevTools → Network tab → найти запрос к `instance.json`
2. Если запроса нет — DockerAdapter не активен; нужно пересобрать `--no-cache` с явным `ENV VITE_SURREALIST_DOCKER=true` в Dockerfile (а не inline в RUN)
3. Если запрос есть и 200 — проблема в парсинге `instance.json` (проверить формат)

**Альтернативное решение:** переключиться на mini-embed режим или просто использовать surrealist.app с WebSocket к localhost:8000

---

## Текущее состояние инфраструктуры

```
make infra     → SurrealDB :8000 (healthy) + MinIO :9000/:9001 (healthy)
make surrealist → Surrealist :8080 (profile: tools)
```

`.env` содержит:
- `SURREAL_USER=root`, `SURREAL_PASS=domovoy_surreal_dev`
- `SURREAL_NS=domovoy`, `SURREAL_DB=domovoy`
- `SURREALIST_VERSION=surrealist-v3.8.5`

---

## Тестовый датасет

`scripts/seed.surql` — 2161 оператор, задействованы все 25 типов рёбер.

Генераторы:
- `scripts/generate_seed.py` — основной датасет (люди, места, техника, медицина, школа, бизнес семян, задачи, плейбуки, авито, документы и т.д.)
- `scripts/generate_forum_seed.py` — wiki-страницы и чаты из forum30.jsonl (yaplakal кулинарный форум)
- `scripts/import_fixtures.py` — загрузка медиафайлов в MinIO + создание `kind: файл` нодов

Залить датасет: `make seed`

Медиафикстуры (пока не залиты):
- Источник изображений: `~/cursor/yascrap/yaplakal-scraper/data/*.jpg`
- Источник видео: `~/shorts/*.mp4`
- Команда: `python3 scripts/import_fixtures.py` (или `--dry-run`)

---

## Архитектура (ключевые решения)

- Одна таблица `thing`, 25 типизированных рёбер
- Все IDs в backticks: `CREATE thing:\`id\` SET field = value;`
- `time::now()` без кавычек, строки в одинарных `'...'`
- SurrealDB v2 API: `POST /sql` с `surreal-ns` / `surreal-db` заголовками
- MinIO S3 API через boto3, файлы хранятся там, в SurrealDB только метаданные
- Воркеры конкурентно захватывают задачи через `UPDATE WHERE status = 'ожидание' AND locked_by = NONE`

---

## Что ещё не сделано

- [ ] Разобраться с Surrealist: почему DockerAdapter не читает instance.json
- [ ] `web/` — инициализировать Next.js проект
- [ ] `worker-scheduler/` — минимальный воркер (cron + counter-триггеры)
- [ ] Залить медиафикстуры (`python3 scripts/import_fixtures.py`)
- [ ] DEFINE-схема в SurrealDB (выжать из docs/database.md)
- [ ] UI-спайки: thing list + detail, граф-визуализация

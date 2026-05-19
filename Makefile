.PHONY: up down logs ps build seed shell-db shell-minio

# ── Dev окружение ─────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

# ── Запуск отдельных сервисов ─────────────────────────────────────────────────

infra:
	docker compose up -d surrealdb minio minio-init

web:
	docker compose up -d web

workers:
	docker compose up -d worker-scheduler worker-playbook worker-bot worker-ai worker-files

# ── База данных ───────────────────────────────────────────────────────────────

seed:
	docker compose exec surrealdb surreal import \
		--conn http://localhost:8000 \
		--user $${SURREAL_USER} --pass $${SURREAL_PASS} \
		--ns $${SURREAL_NS} --db $${SURREAL_DB} \
		/scripts/seed.surql

shell-db:
	docker compose exec surrealdb surreal sql \
		--conn http://localhost:8000 \
		--user $${SURREAL_USER} --pass $${SURREAL_PASS} \
		--ns $${SURREAL_NS} --db $${SURREAL_DB} \
		--pretty

# ── MinIO ─────────────────────────────────────────────────────────────────────

shell-minio:
	docker compose exec minio mc alias set local http://localhost:9000 \
		$${MINIO_USER} $${MINIO_PASS} && \
	docker compose exec minio mc ls local/

# ── Prod ─────────────────────────────────────────────────────────────────────

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

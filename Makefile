.PHONY: up down restart build logs ps infra web workers \
        seed shell-db shell-minio \
        test test-ts test-e2e test-py test-py-ai test-py-files test-clean \
        push deploy up-prod build-prod

REGISTRY   ?= ghcr.io/kscht/domovoy
TAG        := $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)
COMPOSE     = docker compose
COMPOSE_TEST= docker compose -f docker-compose.test.yml
COMPOSE_PROD= docker compose -f docker-compose.yml -f docker-compose.prod.yml

# ── Dev окружение ─────────────────────────────────────────────────────────────

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down && $(COMPOSE) up -d

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

## Только инфраструктура (SurrealDB + MinIO) — удобно при разработке web/workers локально
infra:
	$(COMPOSE) up -d surrealdb minio minio-init

web:
	$(COMPOSE) up -d web

workers:
	$(COMPOSE) up -d worker-scheduler worker-playbook worker-bot worker-ai worker-files

# ── База данных ───────────────────────────────────────────────────────────────

seed:
	$(COMPOSE) exec surrealdb surreal import \
		--conn http://localhost:8000 \
		--user $${SURREAL_USER} --pass $${SURREAL_PASS} \
		--ns $${SURREAL_NS} --db $${SURREAL_DB} \
		/scripts/seed.surql

shell-db:
	$(COMPOSE) exec surrealdb surreal sql \
		--conn http://localhost:8000 \
		--user $${SURREAL_USER} --pass $${SURREAL_PASS} \
		--ns $${SURREAL_NS} --db $${SURREAL_DB} \
		--pretty

shell-minio:
	$(COMPOSE) exec minio mc alias set local http://localhost:9000 \
		$${MINIO_USER} $${MINIO_PASS} && \
	$(COMPOSE) exec minio mc ls local/

# ── Тесты ────────────────────────────────────────────────────────────────────

## Все тесты
test: test-ts test-py

## TypeScript unit + integration тесты
test-ts:
	$(COMPOSE_TEST) run --rm test-ts

## E2E тесты (Playwright)
test-e2e:
	$(COMPOSE_TEST) run --rm test-e2e
	@echo "Артефакты: ./test-results/"

## Все Python тесты
test-py: test-py-ai test-py-files

## Python worker-ai тесты
test-py-ai:
	$(COMPOSE_TEST) run --rm test-py-ai

## Python worker-files тесты
test-py-files:
	$(COMPOSE_TEST) run --rm test-py-files

## Остановить и удалить тестовые контейнеры
test-clean:
	$(COMPOSE_TEST) down --volumes --remove-orphans

# ── Деплой ───────────────────────────────────────────────────────────────────

## Собрать и запушить образы в GHCR
push: build-prod
	docker tag domovoy-web        $(REGISTRY)/web:$(TAG)
	docker tag domovoy-worker-scheduler $(REGISTRY)/worker-scheduler:$(TAG)
	docker tag domovoy-worker-playbook  $(REGISTRY)/worker-playbook:$(TAG)
	docker tag domovoy-worker-bot       $(REGISTRY)/worker-bot:$(TAG)
	docker tag domovoy-worker-ai        $(REGISTRY)/worker-ai:$(TAG)
	docker tag domovoy-worker-files     $(REGISTRY)/worker-files:$(TAG)
	docker push $(REGISTRY)/web:$(TAG)
	docker push $(REGISTRY)/worker-scheduler:$(TAG)
	docker push $(REGISTRY)/worker-playbook:$(TAG)
	docker push $(REGISTRY)/worker-bot:$(TAG)
	docker push $(REGISTRY)/worker-ai:$(TAG)
	docker push $(REGISTRY)/worker-files:$(TAG)
	@echo "Задеплоить: make deploy TAG=$(TAG)"

## Накатить на home-server (ssh)
deploy:
	ssh home-server "cd ~/domovoy && \
		git pull && \
		REGISTRY=$(REGISTRY) TAG=$(TAG) \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans"

## Prod локально (тест prod-конфига)
up-prod:
	$(COMPOSE_PROD) up -d

build-prod:
	$(COMPOSE_PROD) build

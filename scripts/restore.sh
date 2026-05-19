#!/usr/bin/env bash
set -euo pipefail

if [ -f "$(dirname "$0")/../.env" ]; then
  set -a && source "$(dirname "$0")/../.env" && set +a
fi

SURREAL_HOST="${SURREAL_HOST:-localhost}"
SURREAL_PORT="${SURREAL_PORT:-8000}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASS="${SURREAL_PASS:-domovoy_surreal_dev}"
SURREAL_NS="${SURREAL_NS:-domovoy}"
SURREAL_DB="${SURREAL_DB:-domovoy}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_USER="${MINIO_USER:-domovoy}"
MINIO_PASS="${MINIO_PASS:-domovoy_minio_dev}"
MINIO_BUCKET="${MINIO_BUCKET:-domovoy}"

BACKUP_DIR="${1:-}"

if [ -z "$BACKUP_DIR" ]; then
  # Без аргумента — взять последний бэкап
  BACKUP_DIR=$(ls -dt "$(realpath "$(dirname "$0")/../backups")"/[0-9]* 2>/dev/null | head -1)
  if [ -z "$BACKUP_DIR" ]; then
    echo "ERROR: No backups found. Usage: ./restore.sh [backups/TIMESTAMP]"
    exit 1
  fi
  echo "→ Using latest backup: ${BACKUP_DIR}"
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: Backup directory not found: ${BACKUP_DIR}"
  exit 1
fi

SURQL_FILE="${BACKUP_DIR}/surreal.surql"
MINIO_DIR="${BACKUP_DIR}/minio"

if [ ! -f "$SURQL_FILE" ]; then
  echo "ERROR: surreal.surql not found in ${BACKUP_DIR}"
  exit 1
fi

echo "→ Restore from: ${BACKUP_DIR}"

if [ -f "${BACKUP_DIR}/manifest.json" ]; then
  echo "  Manifest:"
  cat "${BACKUP_DIR}/manifest.json" | python3 -m json.tool 2>/dev/null || cat "${BACKUP_DIR}/manifest.json"
fi

echo ""
read -p "  This will OVERWRITE all current data. Continue? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

AUTH=$(echo -n "${SURREAL_USER}:${SURREAL_PASS}" | base64)

# ── Создать namespace и database если нет ────────────────────────────────────
echo "  [1/3] Init namespace/database..."

curl -sf -X POST "http://${SURREAL_HOST}:${SURREAL_PORT}/sql" \
  -H "Accept: application/json" \
  -H "Authorization: Basic ${AUTH}" \
  -d "DEFINE NAMESPACE IF NOT EXISTS ${SURREAL_NS};
      USE NS ${SURREAL_NS};
      DEFINE DATABASE IF NOT EXISTS ${SURREAL_DB};" \
  > /dev/null

echo "  ✓ Namespace and database ready"

# ── Очистить текущие данные ──────────────────────────────────────────────────
echo "  [2/3] Clearing current data..."

curl -sf -X POST "http://${SURREAL_HOST}:${SURREAL_PORT}/sql" \
  -H "Accept: application/json" \
  -H "surreal-ns: ${SURREAL_NS}" \
  -H "surreal-db: ${SURREAL_DB}" \
  -H "Authorization: Basic ${AUTH}" \
  -d "REMOVE DATABASE ${SURREAL_DB};
      USE NS ${SURREAL_NS};
      DEFINE DATABASE ${SURREAL_DB};" \
  > /dev/null

echo "  ✓ Database cleared"

# ── SurrealDB import ─────────────────────────────────────────────────────────
echo "  [3a/3] SurrealDB import..."

HTTP_CODE=$(curl -s -o /tmp/surreal_import_result.json -w "%{http_code}" \
  -X POST "http://${SURREAL_HOST}:${SURREAL_PORT}/import" \
  -H "surreal-ns: ${SURREAL_NS}" \
  -H "surreal-db: ${SURREAL_DB}" \
  -H "Authorization: Basic ${AUTH}" \
  -H "Content-Type: text/plain" \
  --data-binary "@${SURQL_FILE}")

if [ "$HTTP_CODE" != "200" ]; then
  echo "  ERROR: SurrealDB import failed (HTTP ${HTTP_CODE})"
  cat /tmp/surreal_import_result.json
  exit 1
fi

RECORD_COUNT=$(curl -sf -X POST "http://${SURREAL_HOST}:${SURREAL_PORT}/sql" \
  -H "Accept: application/json" \
  -H "surreal-ns: ${SURREAL_NS}" \
  -H "surreal-db: ${SURREAL_DB}" \
  -H "Authorization: Basic ${AUTH}" \
  -d "SELECT count() FROM thing GROUP ALL;" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r[0]['result'][0]['count'] if r[0]['result'] else 0)" 2>/dev/null || echo "?")

echo "  ✓ Imported (${RECORD_COUNT} things)"

# ── MinIO restore ─────────────────────────────────────────────────────────────
if [ -d "$MINIO_DIR" ] && [ "$(ls -A "$MINIO_DIR" 2>/dev/null)" ]; then
  echo "  [3b/3] MinIO restore..."

  docker run --rm \
    --entrypoint sh \
    --network domovoy_default \
    -v "${MINIO_DIR}:/backup" \
    minio/mc:latest \
    -c "mc alias set local http://minio:9000 ${MINIO_USER} ${MINIO_PASS} --quiet &&
        mc mirror /backup local/${MINIO_BUCKET} --overwrite --quiet" 2>/dev/null || \
  docker run --rm \
    --entrypoint sh \
    -v "${MINIO_DIR}:/backup" \
    minio/mc:latest \
    -c "mc alias set local http://${SURREAL_HOST}:${MINIO_PORT} ${MINIO_USER} ${MINIO_PASS} --quiet &&
        mc mirror /backup local/${MINIO_BUCKET} --overwrite --quiet"

  MINIO_FILES=$(find "$MINIO_DIR" -type f | wc -l)
  echo "  ✓ MinIO restored (${MINIO_FILES} files)"
else
  echo "  [3b/3] MinIO: no files in backup, skipping"
fi

echo "✓ Restore complete"

#!/usr/bin/env bash
set -euo pipefail

# Загрузить переменные из .env если запускается напрямую
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

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$(realpath "$(dirname "$0")/../backups/${TIMESTAMP}")"

mkdir -p "${BACKUP_DIR}/minio"

echo "→ Backup: ${BACKUP_DIR}"

# ── SurrealDB export ─────────────────────────────────────────────────────────
echo "  [1/2] SurrealDB export..."

AUTH=$(echo -n "${SURREAL_USER}:${SURREAL_PASS}" | base64)

HTTP_CODE=$(curl -s -o "${BACKUP_DIR}/surreal.surql" -w "%{http_code}" \
  "http://${SURREAL_HOST}:${SURREAL_PORT}/export" \
  -H "surreal-ns: ${SURREAL_NS}" \
  -H "surreal-db: ${SURREAL_DB}" \
  -H "Authorization: Basic ${AUTH}")

if [ "$HTTP_CODE" != "200" ]; then
  echo "  ERROR: SurrealDB export failed (HTTP ${HTTP_CODE})"
  cat "${BACKUP_DIR}/surreal.surql"
  exit 1
fi

SURQL_SIZE=$(wc -c < "${BACKUP_DIR}/surreal.surql")
echo "  ✓ surreal.surql (${SURQL_SIZE} bytes)"

# ── MinIO mirror ─────────────────────────────────────────────────────────────
echo "  [2/2] MinIO mirror..."

docker run --rm \
  --entrypoint sh \
  --network domovoy_default \
  -v "${BACKUP_DIR}/minio:/backup" \
  minio/mc:latest \
  -c "mc alias set local http://minio:9000 ${MINIO_USER} ${MINIO_PASS} --quiet &&
      mc mirror local/${MINIO_BUCKET} /backup --quiet" 2>/dev/null || \
docker run --rm \
  --entrypoint sh \
  -v "${BACKUP_DIR}/minio:/backup" \
  minio/mc:latest \
  -c "mc alias set local http://${SURREAL_HOST}:${MINIO_PORT} ${MINIO_USER} ${MINIO_PASS} --quiet &&
      mc mirror local/${MINIO_BUCKET} /backup --quiet"

MINIO_FILES=$(find "${BACKUP_DIR}/minio" -type f | wc -l)
echo "  ✓ minio/ (${MINIO_FILES} files)"

# ── Манифест ─────────────────────────────────────────────────────────────────
cat > "${BACKUP_DIR}/manifest.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "surreal_ns": "${SURREAL_NS}",
  "surreal_db": "${SURREAL_DB}",
  "minio_bucket": "${MINIO_BUCKET}",
  "surql_bytes": ${SURQL_SIZE},
  "minio_files": ${MINIO_FILES}
}
EOF

echo "✓ Backup complete: backups/${TIMESTAMP}"

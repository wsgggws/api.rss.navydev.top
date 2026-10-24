#!/usr/bin/env bash
set -euo pipefail

NEW_ROOT="${NEW_DEPLOY_ROOT:-$(pwd)}"
LEGACY_ROOT="${LEGACY_DEPLOY_ROOT:-${HOME}/deploy/api.rss.navydev.top}"
NEW_DATA="${NEW_ROOT}/data/postgres"
LEGACY_DATA="${LEGACY_ROOT}/data/postgres"
STAGING="${NEW_ROOT}/data/postgres.migrating-$$"

migration_started=0
committed=0
backup=""
was_running=false

rollback() {
  if [ "${migration_started}" -ne 1 ]; then
    return
  fi

  echo "迁移失败，恢复迁移前的数据库目录。" >&2
  docker stop pg >/dev/null 2>&1 || true
  if [ -d "${NEW_DATA}" ]; then
    mv "${NEW_DATA}" "${NEW_DATA}.failed-$(date +%Y%m%d%H%M%S)"
  fi
  if [ -n "${backup}" ] && [ -d "${backup}" ]; then
    mv "${backup}" "${NEW_DATA}"
  fi
  if [ "${was_running}" = true ]; then
    docker start pg >/dev/null 2>&1 || true
  fi
}

on_exit() {
  status=$?
  if [ "${status}" -ne 0 ] && [ "${committed}" -ne 1 ]; then
    rollback
  fi
  exit "${status}"
}
trap on_exit EXIT

if [ ! -s "${LEGACY_DATA}/PG_VERSION" ]; then
  echo "未发现旧数据库目录 ${LEGACY_DATA}，无需迁移。"
  exit 0
fi

if [ "$(realpath "${LEGACY_DATA}")" = "$(realpath "${NEW_DATA}" 2>/dev/null || true)" ]; then
  echo "新旧数据库目录相同，无需迁移。"
  exit 0
fi

if docker inspect pg >/dev/null 2>&1; then
  was_running="$(docker inspect -f '{{.State.Running}}' pg)"
fi

if [ "${was_running}" = true ]; then
  feed_count="$(docker exec pg psql -U user -d newsdb -tAc 'select count(*) from rss_feed' | tr -d '[:space:]')"
  if [ "${feed_count}" -gt 0 ]; then
    echo "当前数据库已有 ${feed_count} 个订阅源，跳过旧数据迁移。"
    exit 0
  fi
fi

echo "当前数据库为空，从 ${LEGACY_DATA} 迁移旧数据。"
mkdir -p "${NEW_ROOT}/data" "${STAGING}"
docker run --rm --entrypoint sh \
  -v "${LEGACY_DATA}:/from:ro" \
  -v "${STAGING}:/to" \
  postgres:16 \
  -eu -c 'cp -a /from/. /to/'
test -s "${STAGING}/PG_VERSION"

migration_started=1
if docker inspect pg >/dev/null 2>&1; then
  docker stop pg >/dev/null
fi
if [ -d "${NEW_DATA}" ]; then
  backup="${NEW_DATA}.before-migration-$(date +%Y%m%d%H%M%S)"
  mv "${NEW_DATA}" "${backup}"
fi
mv "${STAGING}" "${NEW_DATA}"

if [ "${was_running}" = true ]; then
  docker start pg >/dev/null
  ready=0
  for _ in $(seq 1 30); do
    if docker exec pg pg_isready -U user -d newsdb >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [ "${ready}" -ne 1 ]; then
    echo "迁移后 PostgreSQL 未能就绪。" >&2
    exit 1
  fi
fi

committed=1
echo "旧数据库迁移完成。旧目录备份：${backup:-无（新目录原先不存在）}"

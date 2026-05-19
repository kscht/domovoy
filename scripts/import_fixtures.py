#!/usr/bin/env python3
"""
Импорт тестовых файлов-заглушек в MinIO + создание нодов в SurrealDB.

Берёт:
  - 30 случайных JPEG из ~/cursor/yascrap/yaplakal-scraper/data (реальные фото)
  - 5 самых маленьких видео из ~/shorts

Запуск:
  python3 scripts/import_fixtures.py
  python3 scripts/import_fixtures.py --dry-run
"""
import os
import sys
import json
import random
import argparse
import base64
import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
import httpx

# ─── Конфиг (из .env или дефолты) ───────────────────────────────────────────

def load_env():
    env = {}
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

ENV = load_env()

SURREAL_HOST = ENV.get("SURREAL_HOST", "localhost")
SURREAL_PORT = ENV.get("SURREAL_PORT", "8000")
SURREAL_USER = ENV.get("SURREAL_USER", "root")
SURREAL_PASS = ENV.get("SURREAL_PASS", "domovoy_surreal_dev")
SURREAL_NS   = ENV.get("SURREAL_NS",   "domovoy")
SURREAL_DB   = ENV.get("SURREAL_DB",   "domovoy")
MINIO_HOST   = ENV.get("SURREAL_HOST", "localhost")
MINIO_PORT   = ENV.get("MINIO_PORT",   "9000")
MINIO_USER   = ENV.get("MINIO_USER",   "domovoy")
MINIO_PASS   = ENV.get("MINIO_PASS",   "domovoy_minio_dev")
MINIO_BUCKET = ENV.get("MINIO_BUCKET", "domovoy")

SURREAL_URL = f"http://{SURREAL_HOST}:{SURREAL_PORT}"
MINIO_URL   = f"http://{MINIO_HOST}:{MINIO_PORT}"

HOME = Path.home()
IMAGES_DIR = HOME / "cursor/yascrap/yaplakal-scraper/data"
VIDEOS_DIR = HOME / "shorts"

# ─── Привязка файлов к существующим нодам ────────────────────────────────────
# Файлы будут связаны с этими нодами через ребро `about`

IMAGE_TARGETS = [
    # (thing_id, описание что должно быть на фото)
    ("мотоцикл_bmw_r1250gs",      "фото мотоцикла BMW R1250GS"),
    ("гараж",                      "вид гаража"),
    ("верстак",                    "верстак с инструментами"),
    ("стеллаж_гараж_полка_1",     "стеллаж с инструментами"),
    ("lada_vesta",                 "фото Lada Vesta"),
    ("дача",                       "дача летом"),
    ("сарай",                      "сарай на даче"),
    ("дачный_дом",                 "дачный дом"),
    ("катер_viking_470",           "катер на воде"),
    ("снегоход_arctic_cat_600",   "снегоход зимой"),
    ("квартира",                   "вид квартиры"),
    ("детская",                    "детская комната"),
    ("балкон",                     "балкон"),
    ("кладовка_(подъезд)",         "кладовка"),
    ("полка_с_электроникой_(кабинет)", "полка с электроникой"),
    ("склад_семян_(балкон)",       "семена и саженцы"),
    ("огород_бабушки_(обещанный)", "огород"),
    ("участок",                    "дачный участок"),
    ("погреб",                     "погреб на даче"),
    ("школа_№42",                  "школа снаружи"),
    ("класс_7б",                   "класс в школе"),
    ("поликлиника_№1",             "поликлиника"),
    ("причал_речной_порт",         "речной причал"),
    ("квартира_бабушки",           "квартира бабушки"),
    ("кофры_bmw",                  "кофры мотоцикла"),
    ("багажник_vesta",             "багажник автомобиля"),
    ("смотровая_яма",              "смотровая яма в гараже"),
    ("шкаф_инструментальный",      "инструментальный шкаф"),
    ("кухня",                      "кухня"),
    ("спальня",                    "спальня"),
]

VIDEO_TARGETS = [
    ("мотоцикл_bmw_r1250gs",      "видео поездки на мотоцикле"),
    ("катер_viking_470",           "видео на катере"),
    ("дача",                       "видео с дачи"),
    ("снегоход_arctic_cat_600",   "видео на снегоходе"),
    ("user_papa",                  "семейное видео"),
]

# ─── SurrealDB helper ────────────────────────────────────────────────────────

def surql(query: str) -> list:
    auth = base64.b64encode(f"{SURREAL_USER}:{SURREAL_PASS}".encode()).decode()
    r = httpx.post(
        f"{SURREAL_URL}/sql",
        content=query.encode(),
        headers={
            "Accept": "application/json",
            "surreal-ns": SURREAL_NS,
            "surreal-db": SURREAL_DB,
            "Authorization": f"Basic {auth}",
            "Content-Type": "text/plain",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def surql_str(s):
    return "'" + s.replace("'", "\\'") + "'"

def create_node(tid, **fields):
    parts = []
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, bool):
            parts.append(f"{k} = {str(v).lower()}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k} = {v}")
        else:
            parts.append(f"{k} = {surql_str(str(v))}")
    body = ", ".join(parts)
    return f"CREATE thing:`{tid}` SET {body};"

# ─── MinIO helper ────────────────────────────────────────────────────────────

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_URL,
        aws_access_key_id=MINIO_USER,
        aws_secret_access_key=MINIO_PASS,
        region_name="us-east-1",
    )

def ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=MINIO_BUCKET)
        print(f"  Создан bucket: {MINIO_BUCKET}")

# ─── Выборка файлов ──────────────────────────────────────────────────────────

def pick_images(n=30):
    all_jpgs = list(IMAGES_DIR.rglob("*.jpg"))
    # Фильтр: 50KB – 600KB (реальные фото, не мусор)
    sized = [f for f in all_jpgs if 50_000 < f.stat().st_size < 600_000]
    random.seed(42)
    picked = random.sample(sized, min(n, len(sized)))
    print(f"  Картинки: {len(picked)} из {len(sized)} подходящих (всего {len(all_jpgs)})")
    return picked

def pick_videos(n=5):
    vids = []
    for ext in ["*.mp4", "*.webm", "*.mkv"]:
        vids.extend(VIDEOS_DIR.glob(ext))
    # Берём самые маленькие
    vids.sort(key=lambda f: f.stat().st_size)
    picked = vids[:n]
    print(f"  Видео: {len(picked)} самых маленьких из {len(vids)}")
    for v in picked:
        size_mb = v.stat().st_size / 1_048_576
        print(f"    {v.name} ({size_mb:.1f} MB)")
    return picked

# ─── Основной импорт ─────────────────────────────────────────────────────────

def import_file(s3, path: Path, minio_key: str, thing_id: str,
                description: str, dry_run: bool) -> str | None:
    size = path.stat().st_size
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    kind = "видео" if mime.startswith("video") else "фото"
    fname = path.name

    node_id = f"fixture_{thing_id}_{path.stem[:20]}"
    node_id = node_id.replace(" ", "_").replace("-", "_").replace("'", "")

    if not dry_run:
        # Загрузить в MinIO
        s3.upload_file(
            str(path), MINIO_BUCKET, minio_key,
            ExtraArgs={"ContentType": mime},
        )
        # Создать ноды в SurrealDB
        q = "\n".join([
            create_node(node_id,
                kind="файл",
                subkind=kind,
                name=description,
                filename=fname,
                minio_key=minio_key,
                minio_bucket=MINIO_BUCKET,
                mime_type=mime,
                size_bytes=size,
                status="загружен",
                created_at="time::now()",
            ),
            # файл связан с нодом через about
            f"RELATE thing:`{node_id}`->about->thing:`{thing_id}`;",
            # задача для worker-files: обработать файл
            create_node(f"task_process_{node_id}",
                kind="задача",
                subtype="process-file",
                status="ожидание",
                file_id=f"thing:{node_id}",
                created_at="time::now()",
            ),
            f"RELATE thing:`task_process_{node_id}`->about->thing:`{node_id}`;",
        ])
        results = surql(q)
        errors = [r for r in results if r.get("status") != "OK"]
        if errors:
            print(f"    WARN SurrealDB: {errors}")

    size_kb = size // 1024
    print(f"  {'[dry]' if dry_run else '✓'} {minio_key} ({size_kb}KB) → {thing_id}")
    return node_id

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Не загружать, только показать план")
    parser.add_argument("--images", type=int, default=30)
    parser.add_argument("--videos", type=int, default=5)
    args = parser.parse_args()

    print("=== import_fixtures.py ===")
    print(f"MinIO:   {MINIO_URL}")
    print(f"Surreal: {SURREAL_URL}")
    if args.dry_run:
        print("*** DRY RUN — ничего не загружается ***")
    print()

    if not IMAGES_DIR.exists():
        print(f"WARN: {IMAGES_DIR} не найдена, пропускаю картинки")
        images = []
    else:
        images = pick_images(args.images)

    if not VIDEOS_DIR.exists():
        print(f"WARN: {VIDEOS_DIR} не найдена, пропускаю видео")
        videos = []
    else:
        videos = pick_videos(args.videos)

    print()

    s3 = None
    if not args.dry_run:
        try:
            s3 = get_s3()
            ensure_bucket(s3)
        except Exception as e:
            print(f"ERROR: не могу подключиться к MinIO: {e}")
            sys.exit(1)

    # Загружаем картинки
    if images:
        print("── Картинки ─────────────────────────────────────────────────────────")
        targets = IMAGE_TARGETS * (len(images) // len(IMAGE_TARGETS) + 1)
        for i, (img_path, (target_id, desc)) in enumerate(zip(images, targets)):
            minio_key = f"fixtures/images/img_{i:03d}{img_path.suffix}"
            import_file(s3, img_path, minio_key, target_id, desc, args.dry_run)

    # Загружаем видео
    if videos:
        print()
        print("── Видео ────────────────────────────────────────────────────────────")
        targets = VIDEO_TARGETS * (len(videos) // len(VIDEO_TARGETS) + 1)
        for i, (vid_path, (target_id, desc)) in enumerate(zip(videos, targets)):
            minio_key = f"fixtures/videos/vid_{i:03d}{vid_path.suffix}"
            import_file(s3, vid_path, minio_key, target_id, desc, args.dry_run)

    total = len(images) + len(videos)
    print()
    print(f"{'Готово' if not args.dry_run else 'DRY RUN завершён'}: {total} файлов")
    if not args.dry_run:
        print(f"Запусти make seed (или worker-files) для обработки thumbnails/OCR")

if __name__ == "__main__":
    main()

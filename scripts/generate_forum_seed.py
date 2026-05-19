#!/usr/bin/env python3
"""
Генерирует seed из forum30.jsonl (кулинарный форум ЯПа):
  - kind: страница  — рецепты (wiki для дачи/кухни)
  - kind: чат       — семейные/рабочие чаты
  - kind: сообщение — сообщения в чатах

Запуск:
  python3 scripts/generate_forum_seed.py >> scripts/seed.surql
  или:
  python3 scripts/generate_forum_seed.py > scripts/forum_seed.surql
"""
import json
import re
import random
from pathlib import Path
from datetime import datetime

random.seed(77)

FORUM_JSONL = Path.home() / "cursor/yascrap/yaplakal-scraper/data/forum30.jsonl"

# ─── Очистка текста ───────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Убрать "Это сообщение отредактировал X - дата"
    text = re.sub(r"Это сообщение отредактировал\s+\S+.*?(\n|$)", "", text)
    # Убрать "Занесено в Книгу рецептов ЯПа"
    text = re.sub(r"Занесено в Книгу рецептов ЯПа\s*", "", text)
    # Убрать "X фото" или "X фот"
    text = re.sub(r"\d+\s*фот[оа]?\b\.?\s*", "", text)
    # Убрать "X фото с буквами"
    text = re.sub(r"\d+\s*фото\s+с\s+буквами\.?\s*", "", text)
    # Убрать "просьба не ломать"
    text = re.sub(r"просьба не ломать\.?\s*", "", text)
    # Убрать "Привет, ЯП!" и подобные
    text = re.sub(r"Привет,?\s+ЯП!?\s*", "", text)
    # Убрать "Будет X фото"
    text = re.sub(r"Будет\s+\d+\s+фото\.?\s*", "", text)
    # Убрать цитаты форума "Цитата\n(автор @ дата)\nтекст\n--"
    text = re.sub(r"Цитата\s*\(\S+\s*@[^)]+\)\s*", "", text)
    text = re.sub(r"^Цитата\s*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^--+\s*$", "", text, flags=re.MULTILINE)
    # Убрать ссылки
    text = re.sub(r"https?://\S+", "", text)
    # Лишние пробелы и переносы
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def surql_str(s: str) -> str:
    s = s.replace("\\", "\\\\").replace("'", "\\'")
    return "'" + s + "'"

def create_thing(tid: str, **fields) -> str:
    parts = []
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, bool):
            parts.append(f"{k} = {str(v).lower()}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k} = {v}")
        elif isinstance(v, str) and v.startswith("time::"):
            parts.append(f"{k} = {v}")
        else:
            parts.append(f"{k} = {surql_str(str(v))}")
    return f"CREATE thing:`{tid}` SET {', '.join(parts)};"

def relate(a, edge, b) -> str:
    return f"RELATE thing:`{a}`->{edge}->thing:`{b}`;"

NOW = "time::now()"

# ─── Загрузка данных ──────────────────────────────────────────────────────────

def load_topics():
    topics = []
    with open(FORUM_JSONL) as f:
        for line in f:
            topics.append(json.loads(line))
    return topics

def get_good_topics(topics, min_text=200, min_replies=3):
    good = []
    for t in topics:
        posts = [p for p in t.get("posts", [])
                 if p.get("text", "").strip() and len(p["text"]) >= min_text
                 and not p.get("text", "").startswith("бронь")]
        if len(posts) >= min_replies:
            op = next((p for p in posts if p.get("is_op")), None)
            if op and len(clean_text(op["text"])) >= min_text:
                good.append((t, posts, op))
    return good

# ─── Генерация wiki-страниц (рецепты) ────────────────────────────────────────

RECIPE_TARGETS = [
    # (page_id_suffix, about_node, tag)
    ("dacha_1",  "dacha_garden",    "дача"),
    ("dacha_2",  "dacha_garden",    "дача"),
    ("dacha_3",  "dacha_house",     "дача"),
    ("kitchen_1","apt_kitchen",     "кухня"),
    ("kitchen_2","apt_kitchen",     "кухня"),
    ("kitchen_3","apt_kitchen",     "кухня"),
    ("kitchen_4","apt_kitchen",     "кухня"),
    ("kitchen_5","apt_kitchen",     "кухня"),
    ("user_1",   "user_mama",       "кулинария"),
    ("user_2",   "user_mama",       "кулинария"),
    ("user_3",   "user_papa",       "кулинария"),
    ("dacha_4",  "dacha_shed",      "заготовки"),
    ("dacha_5",  "dacha_cellar",    "заготовки"),
    ("dacha_6",  "dacha_garden",    "огород"),
    ("kitchen_6","apt_kitchen",     "кухня"),
    ("kitchen_7","apt_kitchen",     "кухня"),
    ("dacha_7",  "dacha_house",     "дача"),
    ("user_4",   "user_son",        "рецепты"),
    ("kitchen_8","apt_kitchen",     "кухня"),
    ("dacha_8",  "dacha_garden",    "огород"),
]

def generate_recipe_pages(good_topics):
    lines = []
    lines.append("-- ── Wiki: рецепты из форума ────────────────────────────────────────────")

    selected = random.sample(good_topics, min(len(RECIPE_TARGETS), len(good_topics)))

    for (t, posts, op), (suffix, about_id, tag) in zip(selected, RECIPE_TARGETS):
        title = t["title"][:100]
        body = clean_text(op["text"])
        if len(body) < 100:
            continue

        # Добавим несколько комментариев к телу
        replies = [p for p in posts if not p.get("is_op") and len(clean_text(p["text"])) > 80]
        if replies:
            body += "\n\n---\n\n"
            for r in replies[:3]:
                rtext = clean_text(r["text"])
                if len(rtext) > 50:
                    author = r.get("author") or "Аноним"
                    body += f"**{author}**: {rtext[:300]}\n\n"

        page_id = f"wiki_recipe_{suffix}"
        lines.append(create_thing(page_id,
            kind="страница",
            name=title,
            body=body[:3000],
            tags=tag,
            source="yaplakal-forum30",
            created_at=NOW))
        lines.append(relate(page_id, "about", about_id))
        lines.append(relate("user_mama", "produces", page_id))
        lines.append("")

    return lines

# ─── Генерация чатов ─────────────────────────────────────────────────────────

CHAT_CONFIGS = [
    {
        "chat_id":    "chat_family",
        "name":       "Семейный чат",
        "about":      "user_papa",
        "members":    ["user_papa", "user_mama", "user_son"],
        "n_messages": 15,
        "authors":    ["Папа", "Мама", "Сын"],
    },
    {
        "chat_id":    "chat_dacha",
        "name":       "Чат дача 🌿",
        "about":      "dacha",
        "members":    ["user_papa", "user_mama", "user_grandma"],
        "n_messages": 12,
        "authors":    ["Папа", "Мама", "Бабушка"],
    },
    {
        "chat_id":    "chat_garage",
        "name":       "Гараж / ремонт",
        "about":      "garage",
        "members":    ["user_papa", "neighbor_vasich"],
        "n_messages": 8,
        "authors":    ["Папа", "Васич"],
    },
    {
        "chat_id":    "chat_seeds_business",
        "name":       "Заказы семян",
        "about":      "seeds_business_storage",
        "members":    ["user_mama", "customer_zina", "customer_irina"],
        "n_messages": 10,
        "authors":    ["Мама", "Зинаида Павловна", "Ирина Семёновна"],
    },
    {
        "chat_id":    "chat_class_7b",
        "name":       "Родители 7Б",
        "about":      "school_class_7b",
        "members":    ["user_mama", "teacher_ivanova"],
        "n_messages": 10,
        "authors":    ["Мама", "Иванова Н.П.", "Родитель"],
    },
]

def generate_chats(good_topics):
    lines = []
    lines.append("-- ── Чаты и сообщения ───────────────────────────────────────────────────")

    # Пул коротких постов для сообщений (100-400 символов)
    short_posts = [
        clean_text(p["text"])
        for (t, posts, op) in good_topics
        for p in posts
        if 80 < len(p.get("text","")) < 400 and not p.get("is_op")
           and len(clean_text(p.get("text",""))) > 60
    ]
    random.shuffle(short_posts)
    msg_pool = short_posts[:500]  # возьмём пул из 500

    msg_idx = 0
    for cfg in CHAT_CONFIGS:
        chat_id = cfg["chat_id"]
        lines.append(create_thing(chat_id,
            kind="чат",
            name=cfg["name"],
            created_at=NOW))
        lines.append(relate(chat_id, "about", cfg["about"]))
        for member_id in cfg["members"]:
            lines.append(relate(member_id, "participant", chat_id))
        lines.append("")

        n = cfg["n_messages"]
        authors = cfg["authors"]
        for i in range(n):
            if msg_idx >= len(msg_pool):
                msg_idx = 0
            text = msg_pool[msg_idx][:400]
            msg_idx += 1

            author_name = authors[i % len(authors)]
            author_id = cfg["members"][i % len(cfg["members"])]
            msg_id = f"msg_{chat_id}_{i:03d}"

            lines.append(create_thing(msg_id,
                kind="сообщение",
                body=text,
                author_name=author_name,
                chat_id=f"thing:{chat_id}",
                seq=i,
                created_at=NOW))
            lines.append(relate(msg_id, "part_of", chat_id))
            lines.append(relate(author_id, "produces", msg_id))

        lines.append("")

    return lines

# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    if not FORUM_JSONL.exists():
        print(f"-- ERROR: {FORUM_JSONL} не найден")
        return

    print(f"-- Домовой: wiki-страницы и чаты из forum30.jsonl")
    print(f"-- Сгенерирован: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    topics = load_topics()
    good = get_good_topics(topics)
    print(f"-- Тем в датасете: {len(topics)}, подходящих: {len(good)}")
    print()

    lines = []

    recipe_lines = generate_recipe_pages(good)
    lines.extend(recipe_lines)
    print(f"-- Wiki-страниц (рецепты): {sum(1 for l in recipe_lines if l.startswith('CREATE'))}")

    chat_lines = generate_chats(good)
    lines.extend(chat_lines)
    n_chats = sum(1 for l in chat_lines if "kind = 'чат'" in l)
    n_msgs = sum(1 for l in chat_lines if "kind = 'сообщение'" in l)
    print(f"-- Чатов: {n_chats}, сообщений: {n_msgs}")
    print()

    for line in lines:
        print(line)

    total = sum(1 for l in lines if l.startswith("CREATE") or l.startswith("RELATE"))
    print(f"-- Итого операций forum_seed: {total}")

if __name__ == "__main__":
    main()

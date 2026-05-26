# Аудит `kind` в seed — план миграции

Аналитический документ перед фактической миграцией seed/docs на ASCII-канонические `kind` и 4-классовую онтологию. Не вносит изменений в данные — служит таблицей для одобрения.

Контекст:
- решение про ASCII snake_case как канонический язык — см. диалог по типизации шины;
- решение про 4 класса бытия (item / device / content / living) и тест «`kind` стабилен через лайфсайкл» — там же;
- общая модель типизации связей — [`relation-typing.md`](relation-typing.md);
- **решение про глобальный таксономический словарь** (`vocabulary` + `concept`, SKOS-стиль) — раздел ниже; поглощает прежние отдельные реестры `node_type` / `edge_type` / `category`.

## Исходные числа

- **56 уникальных** значений `kind` в `scripts/seed.surql`
- **1004 узла** с проставленным `kind`
- мигрируем в **~23 канонических** `kind` (схлопывая категории-как-`kind` в `item` + поле `category`; реестры схлопывая в `vocabulary`+`concept`)

## 4 класса бытия — финальная картина

| Класс | Канонические `kind` | Признак |
|---|---|---|
| **item** (пассивная физика) | `item`, `vehicle` | хранится / одалживается / расходуется |
| **device** (физика + сеть) | `device` | hostname, IP, креды, удалённый доступ (PAM) |
| **content** (чистая цифра) | `document`, `document_family`, `file`, `chunk`, `embedding`, `note`, `page`, `message`, `log_entry` | байты / семантика |
| **living** (биологический агент) | `person`, `animal`, `plant` | здоровье, лайфсайкл, забота, неотчуждаемая идентичность |
| места / события / workflow | `location`, `task`, `appeal`, `payment`, `event`, `incident`, `listing`, `diagnosis`, `appointment`, `prescription`, `chat`, `question`, `attempt` | — |
| сущности / группы | `group`, `org` | — |
| шаблоны / теги | `template`, `tag` | — |
| **таксономия (мета)** | `vocabulary`, `concept` | глобальный словарь — поглощает прежние `node_type` / `edge_type` / `category` |

> Конвенция слагов: **snake_case ASCII** (единообразие с предикатами `assigned_to`, `derived_from`).

## Канонический список (целевой)

После миграции — следующие `kind` (29 значений; не все имеют узлы в текущем seed, animal/plant и часть workflow-сущностей добавляются для иллюстрации):

```
Физика:           item, vehicle, device, location                                    (4)
Контент:          document, document_family, file, chunk, embedding,
                  note, page, message, log_entry                                     (9)
Живое:            person, animal, plant                                              (3)
Workflow/события: task, appeal, payment, event, incident, listing, diagnosis        (7)
Сущности:         group, org                                                         (2)
Шаблоны/теги:     template, tag                                                      (2)
Таксономия:       vocabulary, concept                                                (2)
                                                                              итого: 29
```

## Глобальный таксономический словарь

Все «контролируемые перечисления» в системе (типы узлов, типы рёбер, категории item, статусы, роли устройств, виды прав, валюты, языки, MIME, ICD, биологические виды и т.п.) **унифицированы под один шаблон**, выровненный на W3C SKOS (`ConceptScheme` + `Concept`):

- `kind = 'vocabulary'` — узел словаря (= SKOS ConceptScheme)
- `kind = 'concept'` — узел термина внутри словаря (= SKOS Concept)
- `concept → part_of → vocabulary` — членство в словаре
- `concept → part_of → concept` — иерархия (broader/narrower)
- `concept → related_to → concept` — ассоциативная связь (SKOS related)
- `concept → references → external` — ссылка на авторитативный URL (ISO/WHO/schema.org)
- `_i18n` на концепте — `prefLabel` / альтернативные метки по языкам
- `supersedes` — устаревший термин заменён новым

Это **поглощает прежние «три параллельных реестра»** (`node_type`, `edge_type`, `category`) — все три становятся словарями: `vocab:domovoy_kind`, `vocab:domovoy_edge`, `vocab:domovoy_category`. Один паттерн на всё, никаких новых рёбер (все 27 уже покрывают SKOS-семантику).

### Внешние словари — берём как есть

В семейной системе осмысленно подключить (узел `vocabulary`, концепты — наращивать по факту использования, не импортировать целиком):

| Внешний словарь | Где у нас | Что фиксируется |
|---|---|---|
| **ISO 4217** валюты | `payment.currency` | `RUB`/`USD`/`EUR` (уже строки, оборачиваем) |
| **ISO 639** языки | `_lang`, ключи `_i18n` | `ru`/`en`/`de` (уже строки) |
| **ISO 3166** страны | адреса, юрисдикции | `RU`/`KZ` |
| **IANA MIME** | `file.mime` | `application/pdf`, `image/webp` |
| **UN/CEFACT units** | `needs.unit`, `requires.unit` | штуки/литры/кг канонически |
| **ICD-10/11 (WHO)** | `diagnosis.code` | стандартизованные коды диагнозов |
| **ATC** лекарства | `medicine.atc` | классификация препаратов |
| **NCBI Taxonomy / Linnaean** | `animal.species`, `plant.species` | `Solanum lycopersicum`, `Felis catus` |
| **schema.org** | внешние якоря | `references → schema.org/Thing` для интероп |
| **semver** | `requires.constraint` | уже используется (`>=2,<3`) |
| **CPE / CWE / CVE** | `incident.cve` | IT-инциденты |

### Свои словари — то, что заводим

| Словарь | Цель | Размер |
|---|---|---|
| `vocab:domovoy_kind` | 29 канонических `kind` (см. выше) | 29 |
| `vocab:domovoy_edge` | 27 типов рёбер + правила валидации | 27 |
| `vocab:domovoy_category` | категории для `item` (`tool`, `fertilizer`, …) | ~35 |
| `vocab:domovoy_status` | enum статусов (`pending`, `active`, `archived`, …) | ~10 |
| `vocab:domovoy_role` | `role` на `device` (`server`/`workstation`/`router`/…) | ~8 |
| `vocab:domovoy_permission` | права на `can_access` (`view`/`edit`/`share`/`login`/`sudo`) | ~10 |
| `vocab:domovoy_family_role` | роли в семье (`родитель`/`ребёнок`/`опекун`) | ~6 |
| `vocab:domovoy_lifecycle` | стадии для living (`seed`/`sprout`/…/`senescence`) | ~10 |
| `vocab:domovoy_derived_method` | значения `derived_from.method` (`chunk`/`embed`/`thumbnail`/…) | ~7 |

Все живут по одному шаблону. Появилось новое перечислимое поле — заводим новый словарь, без правки схемы.

### Как выглядит

```surql
-- Словарь (внешний — ISO 4217 валюты)
CREATE thing:`vocab_currency` SET
  kind        = 'vocabulary',
  identifier  = 'iso_4217',
  source      = 'external', authority = 'ISO', version = '2024',
  _i18n       = { ru:{label:'Валюты (ISO 4217)'}, en:{label:'Currencies (ISO 4217)'} };

-- Концепт
CREATE thing:`concept_rub` SET
  kind        = 'concept',
  identifier  = 'RUB',
  notation    = '643',
  _i18n       = { ru:{label:'Российский рубль'}, en:{label:'Russian ruble'} };

RELATE thing:`concept_rub`->part_of->thing:`vocab_currency`;
RELATE thing:`concept_rub`->references->thing:`ext_iso_4217_rub` SET mode='link';

-- Использование на узле — поле-slug, ссылается в реестр по identifier
CREATE thing:`pay_inet_jan` SET kind='payment', amount=600, currency='RUB';

-- Иерархия (broader/narrower) — обычный part_of между концептами
RELATE thing:`concept_bone_meal`->part_of->thing:`concept_organic_fertilizer`;
RELATE thing:`concept_organic_fertilizer`->part_of->thing:`concept_fertilizer`;
```

### Градация строгости (как у edge-каталога)

| Режим | Что значит | Когда |
|---|---|---|
| **off** | поле — любая строка, реестр не обязателен | прототипирование, ранний seed |
| **soft** (рекомендую) | лишние значения помечаются линт-воркером, не блокируются | живой граф, постепенный сбор словаря |
| **strict** | `EVENT` валидирует значение против реестра при записи | зрелый граф, UI с автокомплитом |

То же мост к внешнему миру: на `concept` — `references → external` с URL ISO/WHO/schema.org → граф **встраивается в семантический веб без RDF**.

## Полная таблица миграции 56 → 23 (концептуально)

Сортировка по убыванию количества. Колонка «куда» = новый `kind`; «category» = значение поля, если узел уехал в `item`. Категории-слаги — это identifier'ы концептов в `vocab:domovoy_category`.

| Сейчас (`kind`) | # | Куда (`kind`) | category | Класс | Почему |
|---|---:|---|---|---|---|
| `инструмент` | 79 | `item` | `tool` | item | пассивная вещь |
| `место` | 63 | **split** | — | item / location | см. ниже |
| `крепёж` | 62 | `item` | `fastener` | item | |
| `автозапчасть` | 49 | `item` | `auto_part` | item | |
| `книга` | 44 | `item` | `book` | item | бумажные на полке (контент — отдельный `document`) |
| `разное` | 42 | `item` | `misc` | item | |
| `одежда` | 42 | `item` | `clothing` | item | |
| `человек` | 41 | `person` | — | living | |
| `электроника` | 40 | **split** | — | item / device | большинство → item; в сети → device |
| `электрика` | 40 | `item` | `electrical` | item | розетки/провода/выключатели |
| `хозтовар` | 38 | `item` | `household` | item | |
| `спортинвентарь` | 38 | `item` | `sports` | item | вкл. велосипед без учёта пробега |
| `садовый инвентарь` | 38 | `item` | `garden_tool` | item | |
| `медикамент` | 38 | `item` | `medicine` | item | таблетки в аптечке |
| `документ` | 38 | `document` | — | content | |
| `платёж` | 37 | `payment` | — | workflow | |
| `стройматериал` | 31 | `item` | `construction` | item | |
| `электроинструмент` | 25 | `item` | `power_tool` | item | |
| `сантехника` | 23 | `item` | `plumbing` | item | |
| `задача` | 23 | `task` | — | workflow | |
| `семена` | 21 | `item` | `seeds` | item | в seed — пакеты-товар, не растения |
| `автопринадлежность` | 14 | `item` | `auto_accessory` | item | |
| `организация` | 13 | `org` | — | сущность | |
| `снаряжение` | 9 | `item` | `gear` | item | |
| `мотопринадлежность` | 9 | `item` | `moto_accessory` | item | |
| `морское снаряжение` | 9 | `item` | `marine_gear` | item | |
| `страница` | 7 | `page` | — | content | wiki |
| `объявление` | 7 | `listing` | — | workflow | продажа на Авито и т.п. |
| `контакт` | 7 | `person` | — | living | человек вне семьи — всё ещё человек |
| `расходник` | 6 | `item` | `consumable` | item | |
| `заметка` | 6 | `note` | — | content | |
| `саженец` | 5 | `item` | `sapling` | item | в seed — товарные горшки |
| `рыболовное` | 5 | `item` | `fishing` | item | |
| `периферия` | 5 | `item` | `peripheral` | item | мониторы/клавы — пассивны |
| `навигация` | 5 | **split** | — | item / device | бумажные → item; GPS в сети → device |
| `диагноз` | 5 | `diagnosis` | — | мед | |
| `запись` | 4 | `log_entry` | — | content | |
| `гаджет` | 4 | `device` | — | device | смартфоны/планшеты/Kindle |
| `аудио` | 4 | `item` | `audio` | item | bluetooth без сетевого управления |
| `фото/видео` | 3 | `item` | `photo_video` | item | плёнка/диски/фотоальбом |
| `тара` | 3 | `item` | `container` | item | |
| `носитель` | 3 | `item` | `storage_media` | item | флешки/SSD/HDD на полке |
| `компьютер` | 3 | `device` | — | device | |
| `файл` | 2 | `file` | — | content | |
| `туризм` | 2 | `item` | `tourism` | item | мангалы/шатры |
| `субстрат` | 2 | `item` | `substrate` | item | торф/грунт |
| `запчасть` | 2 | `item` | `part` | item | |
| `чанк` | 1 | `chunk` | — | content | |
| `удобрение` | 1 | `item` | `fertilizer` | item | |
| `событие` | 1 | `event` | — | workflow | |
| `сеть` | 1 | `device` | — | device | роутер → `role='router'` |
| `мотор` | 1 | `item` | `engine` | item | мотор катера запасной |
| `документ-семейство` | 1 | `document_family` | — | content | head узла-семейства |
| `агрохимия` | 1 | `item` | `agrochemistry` | item | |
| `embedding` | 1 | `embedding` | — | content | (уже ASCII) |

## Особые случаи: что разделяется

### `место` → `vehicle` (4) + `location` (59)

В seed `kind='место'` сейчас одновременно покрывает два разных класса:

- **Транспорт** (= vehicle, отдельный workflow: пробег, ТО, страховка, журнал поездок):
  - `car_vesta` (Lada Vesta), `moto_bmw` (BMW R1250GS), `boat_viking` (Катер Viking 470), `snowmobile_arctic` (Arctic Cat 600)
- **Локации/контейнеры** (= location, всё остальное): полки, шкафы, помещения, **а также багажники/кофры/ящики/каюты/моторные отсеки внутри транспорта**.

Контейнеры внутри транспорта остаются `location` — они физические подразделения, а не самостоятельные транспортные средства.

### `электроника` и `навигация` → `item` (большинство) + `device` (немногие)

Решение каждого узла — по факту наличия hostname / IP / WiFi-учётки. Конкретный список разберу при миграции.

## Что добавляется (новые `kind`, не было в seed)

| Новый `kind` | Источник | Зачем |
|---|---|---|
| `vehicle` | split из `место` | отдельный workflow транспорта |
| `device` | сборка из гаджет/компьютер/сеть + split электроника | физика+цифра, PAM-семантика прав |
| `location` | переименование `место` (без транспорта) | чистая семантика «место/контейнер» |
| `animal` | — | живые питомцы. **В seed узлов нет** — добавим 1–2 примера (кот) |
| `plant` | — | живые растения. **В seed узлов нет** — добавим 1–2 примера (грядка томатов) |
| `log_entry` | переименование `запись` | журналы (одометр, лог-события) |
| `listing` | переименование `объявление` | торговля |
| `diagnosis` | переименование `диагноз` | медицина |
| `document_family` | переименование `документ-семейство` | head версионирования |
| **`vocabulary`** | новое (мета-словарь) | SKOS-словари (свои + внешние ISO/WHO/schema.org) |
| **`concept`** | новое (термин словаря) | поглощает прежние node_type / edge_type / category |

## Что не входит в этот аудит (не трогаем сейчас)

- `kind` значения, упоминаемые **только в `docs/database.md`** (нет узлов в seed): `server`, `service`, `incident`, `event`, `chat`, `question`, `attempt`, `template`, `tag`. Они уже ASCII или будут добавлены при следующих расширениях.
- Поле `status` — там тоже надо канонизировать значения (`'не начато'` → `'pending'` и т.п.). **Отдельная миграция**, делаем после `kind`; естественно станет `vocab:domovoy_status`.
- Полный импорт внешних словарей (ICD-10 ~70 000 кодов, Linnaean ~миллион видов) — наращиваем concept'ы по факту использования, не bulk-import.

## Категория-как-концепт (не как сырая строка)

В прошлой версии аудита `category` значился «контролируемым словарём из ~30 строк». После решения про SKOS — это **концепты в `vocab:domovoy_category`**, не поле-в-вакууме:

```surql
-- Словарь
CREATE thing:`vocab_category` SET kind='vocabulary', identifier='domovoy_category', source='internal',
  _i18n={ ru:{label:'Категории предметов'}, en:{label:'Item categories'} };

-- Концепт
CREATE thing:`concept_fertilizer` SET kind='concept', identifier='fertilizer',
  _i18n={ ru:{label:'Удобрения'}, en:{label:'Fertilizers'}, de:{label:'Dünger'} };
RELATE thing:`concept_fertilizer`->part_of->thing:`vocab_category`;

-- Иерархия (broader/narrower)
RELATE thing:`concept_organic_fertilizer`->part_of->thing:`concept_fertilizer`;
RELATE thing:`concept_bone_meal`->part_of->thing:`concept_organic_fertilizer`;

-- Использование
CREATE thing:`udobr_npk_5kg` SET kind='item', category='fertilizer', name='Удобрение NPK 5кг';
```

«Жёсткой канонизации» нет — это slug-идентификатор; новый подтип (`bio_fertilizer`, `compost_activator`) = одна `CREATE` без миграции схемы. Soft-режим линта на старте, strict позже.

Полный список ~35 первоначальных `concept`-узлов в `vocab_category`:

```
tool, fastener, auto_part, book, misc, clothing, electronics, electrical,
household, sports, garden_tool, medicine, construction, power_tool, plumbing,
seeds, auto_accessory, gear, moto_accessory, marine_gear, consumable, sapling,
fishing, peripheral, navigation, audio, photo_video, container, storage_media,
tourism, substrate, part, fertilizer, engine, agrochemistry
```

Иерархия — только там, где даёт ценность для запросов («все инструменты» включая `power_tool` и сам `tool`; «всё для огорода» — `garden_tool`/`seeds`/`fertilizer`/`substrate`/`sapling`/`agrochemistry` под `garden_supplies`).

## Чек-лист миграции (после одобрения)

1. **seed.surql — основной массив**:
   - заменить все `kind = 'X'` по таблице;
   - для `item`-узлов добавить поле `category = '...'`;
   - для `device`-узлов — поле `role` (`workstation` / `tablet` / `phone` / `reader` / `router` / `iot`);
   - для `vehicle` — отделить от `location`-контейнеров (4 узла);
   - шапку seed обновить под новый итоговый счёт `kind`.

2. **seed.surql — словари (новый блок в начале)**:
   - **Свои словари** (`vocab:domovoy_kind`, `vocab:domovoy_edge`, `vocab:domovoy_category`) — узел словаря + все концепты с `_i18n` ru/en.
   - **Внешние словари — минимальный набор**: `vocab:iso_4217` (только используемые валюты — RUB, итого 1–3 концепта), `vocab:iso_639` (`ru`, `en`), `vocab:iana_mime` (по факту использования в seed). Узел `external` для авторитативных URL.
   - **Не закладываем** ICD/Linnaean/CPE в этой миграции — добавим, когда появятся узлы, которые их используют.

3. **seed.surql — примеры living** (минимум 4 узла):
   - `pet_murka` (`animal`, кошка) + `located_at`;
   - `tomato_bed_3` (`plant`) + `located_at`;
   - 1 пример `vet_appointment` (`appointment`) для демонстрации reuse мед-паттерна.

4. **docs/relation-typing.md** — обновить:
   - `kind:тип-связи` → `concept` в `vocab:domovoy_edge`;
   - русские `kind`-значения в примерах → ASCII;
   - добавить раздел «Симметричная i18n» (канонические id + `_i18n` метки);
   - добавить упоминание SKOS-унификации со ссылкой на этот аудит.

5. **docs/database.md** — точечно:
   - короткая таблица «4 класса бытия» в начало (после введения);
   - подменить русские `kind` в примерах кода (выборочно — начальные и ключевые разделы).

6. **scripts/generate_seed.py** — обновить генератор под новые `kind` / `category` / реестры (**отдельным коммитом**; runtime не критичен).

Объём: ~1000 строк правок в seed (1-в-1 замены), ~300 новых строк (словари + living + внешние узлы), ~100 строк правок в docs. Один проход.

## Открытые вопросы — нужно решение

1. **`server` и `service`** — оставить отдельными `kind` (как в текущей doc-модели) или схлопнуть `server` в `device` с `role='server'`?
   - **Рекомендация:** схлопнуть. `device` с ролями (workstation/server/router/iot) — единообразно.

2. **`book`** — `item` (бумажная на полке) или собственный `kind` (контент с автором/жанром)?
   - **Рекомендация:** `item` в этом seed (бумажные книги в инвентаре). Контент книги, если появится, — `document` со связью `represents` к физической `item`-книге.

3. **`device`-кандидаты в `электроника`** — конкретный список узлов, которые получают `device` вместо `item`. Сделаю на этапе миграции и приложу мини-таблицу к коммиту.

4. **`role` на `device`** — финальный список: `server`, `workstation`, `tablet`, `phone`, `reader` (Kindle), `router`, `iot`, `appliance`. Добавить?

5. **`animal`/`plant` примеры в seed** — какие именно? Я предложил кошку и грядку томатов как иллюстрации; если у тебя есть конкретные питомцы/растения — лучше реальные.

6. **Внешние словари — стратегия старта** (новое):
   - **(a)** Завести узлы `vocabulary` для ISO 4217 / ISO 639 / IANA MIME сразу, с минимальным набором используемых концептов (`RUB`, `ru`, `en`, `application/pdf`, `image/webp`, …).
   - **(b)** Только `vocabulary`-узлы без концептов, наращивать по первому использованию.
   - **(c)** Ничего не заводить, добавим словари на следующем заходе.
   - **Рекомендация:** (a) — минимальный набор покажет паттерн на живых примерах.

7. **`tag`** как отдельный `kind` или концепт в `vocab:domovoy_tag` (новое)?
   - **Рекомендация:** оставить `kind='tag'` — теги ближе к ad-hoc пользовательским меткам, чем к курируемому словарю. Сохраняет различие «тег vs концепт». Можно пересмотреть позже.

## Резюме одной фразой

> 56 русских `kind`-значений в seed схлопываются в ~23 ASCII-канонических класса; всё, что было «категорией под видом kind», уезжает в поле + концепт в словаре; **все контролируемые перечисления (типы узлов, рёбер, категории, статусы, валюты, MIME, ICD…) унифицированы под SKOS-шаблон `vocabulary` + `concept` без новых рёбер и без RDF**.

Жду одобрения и ответов на 7 вопросов — после этого делаю миграцию одним коммитом.

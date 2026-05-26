# Аудит `kind` в seed — план миграции

Аналитический документ перед фактической миграцией. Решает три задачи сразу:
1. инвентаризация русских `kind`-значений и переход на ASCII-канонические;
2. унификация трёх параллельных реестров под SKOS-шаблон `vocabulary` + `concept`;
3. **соглашение о полях для внешних якорей** (Wikidata / ISO / IANA / WHO / NCBI / CPE) — закладываем структуру сразу, чтобы не переделывать.

Контекст:
- ASCII snake_case как канонический язык — диалог по типизации шины;
- 4 класса бытия (item/device/content/living) и тест «`kind` стабилен через лайфсайкл» — там же;
- модель типизации связей — [`relation-typing.md`](relation-typing.md);
- решение про глобальный таксономический словарь — раздел ниже.

## Исходные числа

- **56 уникальных** значений `kind` в `scripts/seed.surql`
- **1004 узла** с проставленным `kind`
- мигрируем в **29 канонических** `kind`

## 4 класса бытия

| Класс | Канонические `kind` | Признак |
|---|---|---|
| **item** (пассивная физика) | `item`, `vehicle` | хранится / одалживается / расходуется |
| **device** (физика + сеть) | `device` | hostname, IP, креды, удалённый доступ (PAM) |
| **content** (чистая цифра) | `document`, `document_family`, `file`, `chunk`, `embedding`, `note`, `page`, `message`, `log_entry` | байты / семантика |
| **living** (биологический агент) | `person`, `animal`, `plant` | здоровье, лайфсайкл, забота, неотчуждаемая идентичность |
| места / события / workflow | `location`, `task`, `appeal`, `payment`, `event`, `incident`, `listing`, `diagnosis` | — |
| сущности / группы | `group`, `org` | — |
| шаблоны / теги | `template`, `tag` | — |
| **таксономия (мета)** | `vocabulary`, `concept` | словари + термины (SKOS-шаблон) |

## Канонический список kind (29 значений)

```
Физика:           item, vehicle, device, location                                (4)
Контент:          document, document_family, file, chunk, embedding,
                  note, page, message, log_entry                                 (9)
Живое:            person, animal, plant                                          (3)
Workflow/события: task, appeal, payment, event, incident, listing, diagnosis    (7)
Сущности:         group, org                                                     (2)
Шаблоны/теги:     template, tag                                                  (2)
Таксономия:       vocabulary, concept                                            (2)
                                                                          итого: 29
```

Конвенция слагов: **snake_case ASCII** (единообразие с предикатами `assigned_to`, `derived_from`).

## Глобальный таксономический словарь

Все «контролируемые перечисления» (типы узлов/рёбер, категории, статусы, роли, валюты, языки, MIME, ICD, виды и т.п.) унифицированы под W3C SKOS:

- `kind = 'vocabulary'` — узел словаря (ConceptScheme)
- `kind = 'concept'` — узел термина (Concept)
- `concept → part_of → vocabulary` — членство
- `concept → part_of → concept` — иерархия (broader/narrower)
- `concept → related_to → concept` — sameAs / related
- `concept → references → external` — авторитативный URL
- `_i18n` на концепте — prefLabel + переводы
- `supersedes` — устаревший термин заменён

Никаких новых рёбер не нужно — все 27 покрывают SKOS-семантику.

### Свои словари (заводим)

| Словарь | Цель | ≈ Размер |
|---|---|---|
| `vocab:domovoy_kind` | 29 канонических `kind` | 29 |
| `vocab:domovoy_edge` | 27 типов рёбер | 27 |
| `vocab:domovoy_category` | категории item (`tool`, `fertilizer`, ...) | ~35 |
| `vocab:domovoy_brand` | бренды (для item/device/vehicle) | растёт |
| `vocab:domovoy_status` | enum статусов | ~10 |
| `vocab:domovoy_role` | `role` на device (`server`/`workstation`/`router`/...) | ~8 |
| `vocab:domovoy_permission` | права на can_access (`view`/`edit`/`login`/`sudo`/...) | ~10 |
| `vocab:domovoy_family_role` | роли в семье | ~6 |
| `vocab:domovoy_lifecycle` | стадии для living (seed/sprout/.../senescence) | ~10 |
| `vocab:domovoy_derived_method` | значения `derived_from.method` | ~7 |

### Внешние словари (минимальный набор сразу)

| Внешний словарь | Заводить сейчас? | Где используется |
|---|---|---|
| **Wikidata** (`vocab:wikidata`) | **да**, как universal-anchor | поле `wikidata` на любом узле |
| **ISO 4217** валюты | **да**, минимально (RUB+) | `payment.currency` |
| **ISO 639** языки | **да**, минимально (ru, en) | `_lang`, ключи `_i18n` |
| **IANA MIME** | **да**, по факту использования | `file.mime` |
| **ISO 3166** страны | нет, по запросу | адреса |
| **WHO ICD-10/11** | нет, при первом `diagnosis` | `diagnosis.icd` |
| **WHO ATC** лекарства | нет, при первом medicine | `item.atc` |
| **NCBI Taxonomy** | нет, при первом `animal`/`plant` | `animal.taxon_id` |
| **GS1 GTIN** | нет, при первом скане | `item.gtin` |
| **NIST CPE** | нет, при первом `incident` | `device.cpe`, `incident.cpe` |
| **schema.org** | нет | внешние якоря через `references` |

## Соглашение о внешних якорях: поля на узлах

Поля **денормализуют** идентификаторы для скорости и удобства запросов. Авторитативная версия — в графе через `concept` в соответствующем `vocabulary`.

### Универсальное поле `wikidata`

Любой узел может нести поле **`wikidata`** — строку Q-id максимально специфичной сущности Wikidata:

```surql
-- модель есть в Wikidata — указываем модель
CREATE thing:`moto_bmw` SET kind='vehicle', wikidata='Q57821567', ...;     -- BMW R 1250 GS

-- модели нет, есть семейство — указываем семейство
CREATE thing:`laptop_dad` SET kind='device', wikidata='Q861126', ...;       -- ThinkPad (серия)

-- только категория — указываем класс
CREATE thing:`fridge_kitchen` SET kind='item', wikidata='Q37828', ...;      -- refrigerator
```

Через `wikidata` мост к 300+ языкам, GTIN/UNSPSC/GPC/ATC/ICD-маппингам и связанным сущностям — без bulk-импорта.

### Доменно-специфичные идентификаторы

Сиблинги `wikidata`, по необходимости для класса:

| Поле | Класс/контекст | Стандарт |
|---|---|---|
| `gtin` | `item` (покупное) | GS1 GTIN-13 (штрих-код) |
| `isbn` | `item` категории `book` или `document` | ISBN |
| `vin` | `vehicle` | ISO 3779 |
| `license_plate` | `vehicle` | гос. номер |
| `mac` | `device` | IEEE 802 |
| `hostname` | `device` | DNS |
| `imei` | `device` (телефон) | 3GPP |
| `cpe` | `device` (OS/софт), `incident` | NIST CPE |
| `taxon_id` | `animal`, `plant` | NCBI Taxonomy |
| `microchip` | `animal` | ISO 11784/11785 |
| `cultivar` | `plant` | ICRA (Cultivated Plant Code) |
| `atc` | `item` категории `medicine` | WHO ATC |
| `icd` | `diagnosis` | WHO ICD-10/11 |
| `snomed` | `diagnosis` | SNOMED CT |
| `doi` | `document` (научный) | DOI |
| `cve` | `incident` (security) | MITRE CVE |
| `inn`, `ogrn` | `org` (РФ) | ФНС |

### Что несут разные классы

Минимальные обязательные + типичные внешние якоря по классам:

| Класс | Обязательно | Типичные внешние якоря |
|---|---|---|
| `item` | `name`, `category` | `wikidata`, `gtin`, `brand` |
| `vehicle` | `name`, `brand`, `model` | `wikidata`, `vin`, `license_plate` |
| `device` | `name`, `role` | `wikidata`, `mac`, `hostname`, `cpe` (OS), `imei`, `gtin` |
| `person` | `name` | `wikidata` (если общественный), `birth_date` |
| `animal` | `name`, `species` | `wikidata`, `taxon_id`, `microchip` |
| `plant` | `name`, `species`, `stage` | `wikidata`, `taxon_id`, `cultivar` |
| `document` | `name`, `mime` | `isbn`, `doi`, `wikidata` |
| `payment` | `amount`, `currency` (ISO 4217) | `wikidata` (для редких) |
| `diagnosis` | `code` | `icd`, `snomed`, `wikidata` |
| `incident` | `name` | `cve`, `cpe` |
| `org` | `name` | `wikidata`, `inn` / `ogrn` |
| `concept` | `identifier` | `wikidata` (sameAs) |

### `brand` — поле + концепт

Бренд хранится как **slug** на узле (`brand = 'bosch'`) и как **концепт** в `vocab:domovoy_brand`. Концепт несёт `wikidata` Q-id и `_i18n`:

```surql
CREATE thing:`concept_brand_bosch` SET
  kind='concept', identifier='bosch', wikidata='Q234021',
  _i18n={ ru:{label:'Bosch'}, en:{label:'Bosch'} };
RELATE thing:`concept_brand_bosch`->part_of->thing:`vocab_domovoy_brand`;
```

## Стартовый набор концептов с Wikidata Q-id (верифицировано)

Q-id подтверждены через `wbsearchentities`. Заводим в seed для каждого с привязкой к нашим `concept`-узлам.

### Категории (`vocab:domovoy_category` → Wikidata)

| Наш `category` | Wikidata Q-id | Wikidata label |
|---|---|---|
| `laptop` | Q3962 | laptop / ноутбук |
| `refrigerator` | Q37828 | refrigerator / холодильник |
| `washing_machine` | Q124441 | washing machine |
| `dishwasher` | Q186263 | dishwasher |
| `microwave` | Q127956 | microwave oven |
| `air_conditioner` | Q1265533 | air conditioner |
| `electric_kettle` | Q1364042 | electric kettle |
| `oven` | Q36539 | oven |
| `coffeemaker` | Q211841 | coffeemaker |
| `vacuum_cleaner` | Q101674 | vacuum cleaner |
| `power_tool` | Q1327701 | power tool |
| `rotary_hammer` | Q1932875 | rotary hammer |
| `fertilizer` | Q83323 | fertilizer |
| `book` | (категория, узкая привязка через `wikidata` на узле) | book |
| `bicycle` | Q11442 | bicycle |
| `motorcycle` | Q34493 | motorcycle |
| `car` | Q1420 | car |

### Бренды (`vocab:domovoy_brand` → Wikidata)

| Наш `brand` | Wikidata Q-id |
|---|---|
| `apple` | Q312 |
| `bmw` | Q26678 |
| `bosch` | Q234021 |
| `lenovo` | Q14799 |
| `makita` | Q691508 |

### Конкретные модели в seed (поле `wikidata` прямо на узле)

| Узел seed | Wikidata Q-id | Что |
|---|---|---|
| `moto_bmw` | **Q57821567** | BMW R 1250 GS |
| `car_vesta` | **Q17376334** | Lada Vesta |

### Внешний словарь Wikidata — как выглядит

```surql
CREATE thing:`vocab_wikidata` SET
  kind='vocabulary', identifier='wikidata', source='external',
  authority='Wikimedia Foundation', version='live',
  _i18n={ ru:{label:'Wikidata'}, en:{label:'Wikidata'} };

-- Наш концепт ↔ Wikidata концепт
CREATE thing:`concept_dom_laptop` SET
  kind='concept', identifier='laptop', wikidata='Q3962',
  _i18n={ ru:{label:'Ноутбук'}, en:{label:'Laptop'} };
RELATE thing:`concept_dom_laptop`->part_of->thing:`vocab_domovoy_category`;

-- Если хотим материализовать концепт самой Wikidata (для иерархии/линка на URL):
CREATE thing:`concept_wd_q3962` SET kind='concept', identifier='Q3962';
RELATE thing:`concept_wd_q3962`->part_of->thing:`vocab_wikidata`;
RELATE thing:`concept_dom_laptop`->related_to->thing:`concept_wd_q3962` SET label='sameAs';
```

Материализация концептов Wikidata — **лениво**: только когда нужна иерархия (broader/narrower через part_of) или прямая ссылка на URL.

## Полная таблица миграции 56 → 29

Сортировка по убыванию количества.

| Сейчас (`kind`) | # | Куда (`kind`) | category | wikidata-якорь (категории) | Класс |
|---|---:|---|---|---|---|
| `инструмент` | 79 | `item` | `tool` | Q39546 (tool) | item |
| `место` | 63 | **split** | — | — | item / location |
| `крепёж` | 62 | `item` | `fastener` | — | item |
| `автозапчасть` | 49 | `item` | `auto_part` | — | item |
| `книга` | 44 | `item` | `book` | — | item |
| `разное` | 42 | `item` | `misc` | — | item |
| `одежда` | 42 | `item` | `clothing` | — | item |
| `человек` | 41 | `person` | — | Q5 (для класса) | living |
| `электроника` | 40 | **split** | — | — | item / device |
| `электрика` | 40 | `item` | `electrical` | — | item |
| `хозтовар` | 38 | `item` | `household` | — | item |
| `спортинвентарь` | 38 | `item` | `sports` | — | item |
| `садовый инвентарь` | 38 | `item` | `garden_tool` | — | item |
| `медикамент` | 38 | `item` | `medicine` | — | item |
| `документ` | 38 | `document` | — | — | content |
| `платёж` | 37 | `payment` | — | — | workflow |
| `стройматериал` | 31 | `item` | `construction` | — | item |
| `электроинструмент` | 25 | `item` | `power_tool` | Q1327701 | item |
| `сантехника` | 23 | `item` | `plumbing` | — | item |
| `задача` | 23 | `task` | — | — | workflow |
| `семена` | 21 | `item` | `seeds` | — | item |
| `автопринадлежность` | 14 | `item` | `auto_accessory` | — | item |
| `организация` | 13 | `org` | — | — | сущность |
| `снаряжение` | 9 | `item` | `gear` | — | item |
| `мотопринадлежность` | 9 | `item` | `moto_accessory` | — | item |
| `морское снаряжение` | 9 | `item` | `marine_gear` | — | item |
| `страница` | 7 | `page` | — | — | content |
| `объявление` | 7 | `listing` | — | — | workflow |
| `контакт` | 7 | `person` | — | — | living |
| `расходник` | 6 | `item` | `consumable` | — | item |
| `заметка` | 6 | `note` | — | — | content |
| `саженец` | 5 | `item` | `sapling` | — | item |
| `рыболовное` | 5 | `item` | `fishing` | — | item |
| `периферия` | 5 | `item` | `peripheral` | — | item |
| `навигация` | 5 | **split** | — | — | item / device |
| `диагноз` | 5 | `diagnosis` | — | — | мед |
| `запись` | 4 | `log_entry` | — | — | content |
| `гаджет` | 4 | `device` | — | — | device |
| `аудио` | 4 | `item` | `audio` | — | item |
| `фото/видео` | 3 | `item` | `photo_video` | — | item |
| `тара` | 3 | `item` | `container` | — | item |
| `носитель` | 3 | `item` | `storage_media` | — | item |
| `компьютер` | 3 | `device` | — | — | device |
| `файл` | 2 | `file` | — | — | content |
| `туризм` | 2 | `item` | `tourism` | — | item |
| `субстрат` | 2 | `item` | `substrate` | — | item |
| `запчасть` | 2 | `item` | `part` | — | item |
| `чанк` | 1 | `chunk` | — | — | content |
| `удобрение` | 1 | `item` | `fertilizer` | Q83323 | item |
| `событие` | 1 | `event` | — | — | workflow |
| `сеть` | 1 | `device` | — | — | device |
| `мотор` | 1 | `item` | `engine` | — | item |
| `документ-семейство` | 1 | `document_family` | — | — | content |
| `агрохимия` | 1 | `item` | `agrochemistry` | — | item |
| `embedding` | 1 | `embedding` | — | — | content |

## Особые случаи

### `место` → `vehicle` (4) + `location` (59)

Транспорт (отдельный `kind='vehicle'`, поле `wikidata`):
- `car_vesta` → `vehicle` + `wikidata='Q17376334'`
- `moto_bmw` → `vehicle` + `wikidata='Q57821567'`
- `boat_viking` → `vehicle`
- `snowmobile_arctic` → `vehicle`

Остальное — `location` (включая багажники/кофры/каюты — они контейнеры внутри транспорта).

### `электроника` и `навигация` → `item` (большинство) + `device` (немногие)

Решение пер-узел: hostname/IP/WiFi-учётка → `device`, иначе → `item`. Конкретный список разберу при миграции и приложу.

## Что добавляется (новые `kind`, не было в seed)

| Новый `kind` | Источник |
|---|---|
| `vehicle` | split из `место` |
| `device` | сборка из гаджет/компьютер/сеть + split электроника |
| `location` | переименование `место` (без транспорта) |
| `animal` | новый класс (примеры: кот Murka) |
| `plant` | новый класс (примеры: грядка томатов) |
| `log_entry` | переименование `запись` |
| `listing` | переименование `объявление` |
| `diagnosis` | переименование `диагноз` |
| `document_family` | переименование `документ-семейство` |
| `vocabulary` | новый мета — SKOS-словари |
| `concept` | новый мета — термины |

## Что не входит в этот аудит

- `kind`-значения, упоминаемые только в `docs/database.md`: `server`, `service`, `incident`, `event`, `chat`, `question`, `attempt`, `template`, `tag` — добавим при расширениях.
- Поле `status` — отдельная миграция, после `kind`; станет `vocab:domovoy_status`.
- Bulk-импорт внешних словарей (ICD-10/Linnaean/CPE) — лениво, концепты по факту использования.

## Категория-как-концепт

Каждое значение поля `category` — это **slug**, ссылающийся в `vocab:domovoy_category` по `identifier`. Концепт несёт `_i18n` метки и `wikidata` Q-id класса.

```surql
CREATE thing:`udobr_npk_5kg` SET kind='item', category='fertilizer',
  brand='bosch', wikidata='Q83323',   -- класс «удобрение» / можно опустить
  name='Удобрение NPK 5кг';
```

Иерархия (broader/narrower) — через `part_of` между концептами; только там, где имеет смысл для запросов.

## Чек-лист миграции (после одобрения)

1. **seed.surql — основной массив (1004 узла)**:
   - заменить все `kind = 'X'` по таблице;
   - для `item`-узлов добавить `category` (slug);
   - для `vehicle`-узлов добавить `brand`, `model`, `wikidata` (где есть Q-id);
   - для `device`-узлов добавить `role`, опц. `mac`/`hostname`/`wikidata`;
   - 4 узла из `место` отделить в `vehicle`;
   - 13 узлов `контакт` мигрировать в `person` с `participant {role:'contact'}` или полем;
   - шапку seed обновить под новый итог.

2. **seed.surql — словари (новый блок в начале)**:
   - **Свои**: `vocab:domovoy_kind` (29 концептов), `vocab:domovoy_edge` (27), `vocab:domovoy_category` (~35), `vocab:domovoy_brand` (5 стартовых: apple/bmw/bosch/lenovo/makita).
   - **Внешние стартовые**: `vocab:wikidata` (узел словаря + ~20 концептов из таблицы выше), `vocab:iso_4217` (RUB+ при необходимости), `vocab:iso_639` (ru, en), `vocab:iana_mime` (по факту).
   - **Cross-links**: для каждого `concept` в `vocab:domovoy_category` поле `wikidata=Q...` (где есть); опц. `related_to {label:'sameAs'} → concept_wd_QXXX`.

3. **seed.surql — примеры living + внешние якоря**:
   - `pet_murka` (`animal`, кошка) + `wikidata='Q146'` + `located_at`;
   - `tomato_bed_3` (`plant`) + `wikidata='Q23501'` + `located_at`;
   - 1 `appointment` для демонстрации reuse мед-паттерна.

4. **docs/relation-typing.md** — обновить примеры под ASCII-`kind` + SKOS-унификацию.

5. **docs/database.md** — добавить:
   - короткую таблицу «4 класса бытия»;
   - раздел «Внешние якоря: соглашение о полях» с таблицей по классам;
   - подменить русские `kind` в примерах кода (выборочно).

6. **scripts/generate_seed.py** — обновить генератор (отдельным коммитом).

Объём: ~1000 строк правок в seed, ~400 новых строк (словари + концепты + living + внешние), ~150 строк правок в docs. Один проход.

## Открытые вопросы

1. **`server` и `service`** — `server` схлопнуть в `device` с `role='server'`?
   *Рекомендация: схлопнуть.*

2. **`book`** — `item` (бумажная) или собственный `kind`?
   *Рекомендация: `item` в этом seed; контент книги — отдельный `document` + `represents` к item-книге.*

3. **`device`-кандидаты в `электроника`** — список приложу при миграции.

4. **`role` на `device`** — финальный список: `server`, `workstation`, `tablet`, `phone`, `reader`, `router`, `iot`, `appliance`. Добавить?

5. **`animal`/`plant` примеры** — кошка + грядка томатов, или реальные твои?

6. **`tag`** — отдельный `kind` или концепт в `vocab:domovoy_tag`?
   *Рекомендация: оставить `kind='tag'` (теги — ad-hoc пользовательские, не курируемый словарь).*

7. **`wikidata` поле — на каждом узле или только где есть?**
   *Рекомендация: optional, заводим где есть Q-id. Денормализация для скорости; авторитет в графе через концепт.*

8. **Стратегия материализации внешних концептов** — заводить `concept`-узел Wikidata каждый раз, когда указали `wikidata=Q...` на любом узле, или лениво по требованию (только когда нужны иерархия/URL)?
   *Рекомендация: лениво. Поле `wikidata` достаточно для 95% запросов; материализация концепта — когда нужны связи.*

## Резюме

> 56 русских `kind`-значений → 29 ASCII-канонических; категории-под-видом-kind уезжают в поле + концепт в словаре; контролируемые перечисления унифицированы под SKOS (`vocabulary` + `concept`) **без новых рёбер**; внешние якоря (Wikidata Q-id, ISO коды, GTIN/ISBN/VIN/CVE/...) — **денормализованные поля на узлах** с парным концептом в графе; верифицированный стартовый набор Wikidata Q-id для уже существующих сущностей в seed заложен сразу, чтобы потом не переделывать структуру.

Жду одобрения и ответов на 8 вопросов — после этого миграция одним коммитом.

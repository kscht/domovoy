# Аудит `kind` в seed — план миграции

Аналитический документ перед фактической миграцией seed/docs на ASCII-канонические `kind` и 4-классовую онтологию. Не вносит изменений в данные — служит таблицей для одобрения.

Контекст:
- решение про ASCII snake_case как канонический язык — см. диалог по типизации шины;
- решение про 4 класса бытия (item / device / content / living) и тест «`kind` стабилен через лайфсайкл» — там же;
- общая модель типизации связей — [`relation-typing.md`](relation-typing.md).

## Исходные числа

- **56 уникальных** значений `kind` в `scripts/seed.surql`
- **1004 узла** с проставленным `kind`
- мигрируем в **~25 канонических** `kind` (схлопывая категории-как-`kind` в `item` + поле `category`)

## 4 класса бытия — финальная картина

| Класс | Канонические `kind` | Признак |
|---|---|---|
| **item** (пассивная физика) | `item`, `vehicle` | хранится / одалживается / расходуется |
| **device** (физика + сеть) | `device` | hostname, IP, креды, удалённый доступ (PAM) |
| **content** (чистая цифра) | `document`, `document_family`, `file`, `chunk`, `embedding`, `note`, `page`, `message`, `log_entry` | байты / семантика |
| **living** (биологический агент) | `person`, `animal`, `plant` | здоровье, лайфсайкл, забота, неотчуждаемая идентичность |
| места / события / workflow | `location`, `task`, `appeal`, `payment`, `event`, `incident`, `listing`, `diagnosis`, `appointment`, `prescription`, `chat`, `question`, `attempt` | — |
| сущности / группы | `group`, `org` | — |
| таксономия / шаблоны / мета | `category`, `template`, `tag`, `node_type`, `edge_type` | — |

> Конвенция слагов: **snake_case ASCII** (единообразие с предикатами `assigned_to`, `derived_from`).

## Канонический список (целевой)

25 значений `kind` после миграции:

```
item, vehicle, device,
document, document_family, file, chunk, embedding, note, page, message, log_entry,
person, animal, plant,
location,
task, appeal, payment, event, incident, listing, diagnosis,
group, org,
category, template, tag,
node_type, edge_type
```

(30 строк выше, но `animal` и `plant` пока узлов в seed не имеют — добавляем как примеры; `incident`, `event`, `listing`, `diagnosis`, `chat`, `question`, `attempt` и др. — частично уже есть, частично появятся.)

## Полная таблица миграции 56 → 25

Сортировка по убыванию количества. Колонка «куда» = новый `kind`; «category» = значение поля, если узел уехал в `item`.

| Сейчас (`kind`) | # | Куда (`kind`) | category | Класс | Почему |
|---|---:|---|---|---|---|
| `инструмент` | 79 | `item` | `tool` | item | пассивная вещь |
| `место` | 63 | **split** | — | item / location | см. ниже |
| `крепёж` | 62 | `item` | `fastener` | item | |
| `автозапчасть` | 49 | `item` | `auto_part` | item | |
| `книга` | 44 | `item` | `book` | item | бумажные на полке (контент книги — отдельный `document`) |
| `разное` | 42 | `item` | `misc` | item | |
| `одежда` | 42 | `item` | `clothing` | item | |
| `человек` | 41 | `person` | — | living | системный класс уже есть |
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
| `семена` | 21 | `item` | `seeds` | item | в seed — пакеты-товар, не растения. Когда посадят — отдельный `plant`-узел через `derived_from` |
| `автопринадлежность` | 14 | `item` | `auto_accessory` | item | |
| `организация` | 13 | `org` | — | сущность | |
| `снаряжение` | 9 | `item` | `gear` | item | |
| `мотопринадлежность` | 9 | `item` | `moto_accessory` | item | |
| `морское снаряжение` | 9 | `item` | `marine_gear` | item | |
| `страница` | 7 | `page` | — | content | wiki |
| `объявление` | 7 | `listing` | — | workflow | продажа на Авито и т.п. |
| `контакт` | 7 | `person` | — | living | человек вне семьи — всё ещё человек. Различие через ребро `participant {role:'contact'}` или поле |
| `расходник` | 6 | `item` | `consumable` | item | |
| `заметка` | 6 | `note` | — | content | |
| `саженец` | 5 | `item` | `sapling` | item | в seed — товарные горшки. После посадки → отдельный `plant` |
| `рыболовное` | 5 | `item` | `fishing` | item | |
| `периферия` | 5 | `item` | `peripheral` | item | мониторы/клавы/мыши — пассивны |
| `навигация` | 5 | **split** | — | item / device | бумажные карты/компас → item; GPS-приёмник в сети → device |
| `диагноз` | 5 | `diagnosis` | — | workflow/мед | |
| `запись` | 4 | `log_entry` | — | content | одометр, журналы |
| `гаджет` | 4 | `device` | — | device | смартфоны/планшеты/Kindle — все в сети, с аккаунтами |
| `аудио` | 4 | `item` | `audio` | item | bluetooth-наушники/колонки без сетевого управления |
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
| `сеть` | 1 | `device` | — | device | роутер TP-Link → `role='router'` |
| `мотор` | 1 | `item` | `engine` | item | мотор катера запасной |
| `документ-семейство` | 1 | `document_family` | — | content | head узла-семейства для версий (`reglament_to_bmw`) |
| `агрохимия` | 1 | `item` | `agrochemistry` | item | |
| `embedding` | 1 | `embedding` | — | content | (уже ASCII) |

## Особые случаи: что разделяется

### `место` → `vehicle` (4) + `location` (59)

В seed `kind='место'` сейчас одновременно покрывает два разных класса:

- **Транспорт** (= vehicle, отдельный workflow: пробег, ТО, страховка, журнал поездок):
  - `car_vesta` (Lada Vesta)
  - `moto_bmw` (BMW R1250GS)
  - `boat_viking` (Катер Viking 470)
  - `snowmobile_arctic` (Снегоход Arctic Cat 600)
- **Локации/контейнеры** (= location, всё остальное): полки, шкафы, помещения, **а также багажники/кофры/ящики/каюты/моторные отсеки внутри транспорта**.

Контейнеры внутри транспорта остаются `location` — они физические подразделения, а не самостоятельные транспортные средства.

### `электроника` → `item` (большинство) + `device` (немногие)

В seed под `электроника` стоят и пассивные вещи (ESP8266 в коробке, мелочи), и потенциально-сетевые. Решение каждого — по факту: есть hostname / IP / WiFi-учётка → `device`, иначе → `item` (`category='electronics'`). Конкретный список разберу при миграции.

### `навигация` → `item` (4) + `device` (1)

Аналогично: бумажные карты/компас/наклейки → `item` (`category='navigation'`); GPS-устройство с сетью/аккаунтом → `device`.

## Что добавляется (новые `kind`, не было в seed)

| Новый `kind` | Источник | Зачем |
|---|---|---|
| `vehicle` | split из `место` | отдельный workflow транспорта |
| `device` | сборка из гаджет/компьютер/сеть + split электроника | физика+цифра, PAM-семантика прав |
| `location` | переименование `место` (без транспорта) | чистая семантика «место/контейнер» |
| `animal` | — | живые питомцы. **В seed узлов пока нет** — добавим 1–2 примера для иллюстрации (кот, собака) |
| `plant` | — | живые растения (грядки). **В seed узлов пока нет** — добавим 1–2 примера (томаты, яблоня) |
| `log_entry` | переименование `запись` | журналы (одометр, лог-события) |
| `listing` | переименование `объявление` | торговля |
| `diagnosis` | переименование `диагноз` | медицина |
| `document_family` | переименование `документ-семейство` | head версионирования |
| `node_type` | новое (реестр) | словарь типов узлов с `_i18n` |
| `edge_type` | новое (реестр) | словарь типов связей (был `тип-связи` в плане) |

## Что не входит в этот аудит (не трогаем сейчас)

- `kind` значения, упоминаемые **только в `docs/database.md`** (нет узлов в seed): `server`, `service`, `incident`, `event` (помимо 1 экземпляра), `chat`, `question`, `attempt`, `template`, `category`, `tag`. Они уже ASCII или будут добавлены при следующих расширениях. Конвенция применяется к ним автоматически.
- Поле `status` — там тоже надо канонизировать значения (`'не начато'` → `'pending'` и т.п.). **Отдельная миграция**, делаем после `kind`.

## Категория-как-поле — новый словарь

Все «было-категорийные» `kind` уходят в поле `category`. Полный список значений `category` после миграции (≈30):

```
tool, fastener, auto_part, book, misc, clothing, electronics, electrical,
household, sports, garden_tool, medicine, construction, power_tool, plumbing,
seeds, auto_accessory, gear, moto_accessory, marine_gear, consumable, sapling,
fishing, peripheral, navigation, audio, photo_video, container, storage_media,
tourism, substrate, part, fertilizer, engine, agrochemistry
```

(Категории — это контролируемый словарь; в перспективе — узлы `kind='category'` с `_i18n` для UI.)

## Чек-лист миграции (после одобрения)

1. **seed.surql** — основной массив:
   - заменить все `kind = 'X'` по таблице;
   - для `item`-узлов добавить поле `category = '...'`;
   - для `device`-узлов — поля `role` (`workstation` / `tablet` / `phone` / `reader` / `router` / `iot`);
   - для `vehicle` — отделить от `location`-контейнеров (4 узла);
   - в шапке seed-файла обновить «все 27 типов рёбер» (без изменений, рёбер не трогаем).
2. **seed.surql — реестр** (новый блок в начале):
   - `kind='node_type'` для каждого канонического `kind` с `_i18n` (ru/en);
   - `kind='edge_type'` для ключевых рёбер (assigned_to, depends_on, derived_from, can_access, contains, located_at) с `from_kinds`/`to_kinds`/`_i18n`.
3. **seed.surql — примеры living** (минимум 4 узла):
   - `pet_murka` (`animal`, кошка) + ребро `located_at`;
   - `tomato_bed_3` (`plant`) + ребро `located_at`;
   - 1 пример `vet_appointment` для демонстрации reuse мед-паттерна.
4. **docs/relation-typing.md** — обновить примеры:
   - `kind:тип-связи` → `kind='edge_type'` в slug;
   - русские `kind`-значения в примерах → ASCII;
   - добавить раздел «Симметричная i18n» (канонические id + `_i18n` метки).
5. **docs/database.md** — точечно:
   - короткая таблица «4 класса бытия» в начало (после введения);
   - подменить русские `kind` в примерах кода (не все 9800 строк, а только примеры в начале и в разделах кода).
6. **scripts/generate_seed.py** — обновить генератор под новые `kind`/`category` (отдельным коммитом; runtime сейчас не критичен).

Объём: ~1000 строк правок в seed (1-в-1 замены), 200 новых строк (реестр + living), 100 строк правок в docs. Один проход.

## Открытые вопросы — нужно решение

1. **`server` и `service`** — оставить отдельными `kind` (как в текущей doc-модели) или схлопнуть `server` в `device` с `role='server'`?
   - **Рекомендация:** схлопнуть. `device` с ролями (workstation/server/router/iot) — единообразно.
   - **Против:** в IT-домене «сервер» и «сервис» — устоявшиеся термины, отдельные `kind` дают чистые запросы (`WHERE kind='server'`). Но это решается через `WHERE kind='device' AND role='server'`.

2. **`book`** — `item` (бумажная на полке) или собственный `kind` (контент с автором/жанром/прочитанностью)?
   - **Рекомендация:** `item` в этом seed (там бумажные книги в инвентаре, без контента). Если позже захочется learning-домен — отдельный `kind` `book` ИЛИ хранение содержимого как `document` со связью `represents` к физической `item`-книге.

3. **`сantчик` / `electronics` split** — конкретный список узлов, которые получают `device` вместо `item`. Сделаю на этапе миграции и приложу к коммиту мини-таблицу.

4. **`role` на `device`** — финальный список значений: `server`, `workstation`, `tablet`, `phone`, `reader` (Kindle), `router`, `iot`, `appliance`. Если что-то добавить — скажи.

5. **`animal`/`plant` примеры в seed** — какие именно? Я предложил кошку и грядку томатов как иллюстрации; если у тебя есть конкретные питомцы/растения — лучше реальные.

## Резюме одной фразой

> 56 русских `kind`-значений в seed схлопываются в 25 ASCII-канонических классов; всё, что было «категорией под видом kind», уезжает в поле `category` и появляется реестр-словарь с `_i18n` для UI на любом языке.

Жду одобрения списка и ответов на 5 вопросов выше — после этого делаю миграцию одним коммитом.

# Структура базы данных (SurrealDB)

## Концепция

Всё есть **вещь** (`thing`). Гараж, полка, мотоцикл, масло, рецепт, магазин, человек, семья,
задача, подзадача, платёж, обращение, инстанция — один тип узла.
Смысл задаётся только рёбрами (связями) между вещами.

---

## Узлы

| Таблица | Примеры |
|---------|---------|
| `thing` | предмет, место, контейнер, транспорт, человек, группа, задача, подзадача, рецепт, процедура, запуск, список, платёж, обращение, решение, инстанция |

Типичные поля по смыслу:

| Смысл | Поля |
|-------|------|
| Любая вещь | `name`, `description`, `notes` |
| Физический предмет | `quantity`, `unit`, `purchase_date`, `price` |
| Задача / обращение | `status`, `deadline`, `priority` |
| Периодический платёж | `amount`, `period`, `due_day`, `paid_until` |
| Человек | `role` (папа, мама, сын, дочь, бабушка) |
| Физическая/цифровая вещь | `kind` (физическое / цифровое / смешанное) |

**`status`:** `не начато` / `в процессе` / `выполнено` / `ожидает` / `отменено`  
**`period`:** `ежедневно` / `еженедельно` / `ежемесячно` / `ежеквартально` / `ежегодно`

---

## Рёбра

| Связь | Описание | Поля на ребре |
|-------|----------|---------------|
| `contains` | Где физически находится вещь | `reason`, `since` |
| `part_of` | Часть чего / подзадача / запуск шаблона | — |
| `assigned_to` | Кто отвечает (человек, группа или вся семья) | — |
| `depends_on` | Задача ждёт выполнения другой | — |
| `about` | Задача/обращение касается этой вещи или решения | — |
| `filed_with` | Обращение подано в эту инстанцию/организацию | — |
| `needs` | Что нужно купить (список → вещь) | `quantity`, `unit` |
| `requires` | Плановый расход (шаблон → ингредиент/деталь) | `quantity`, `unit` |
| `produces` | Результат выполнения (решение, документ, блюдо) | — |
| `used` | Фактический расход при запуске | `quantity`, `unit` |
| `represents` | Цифровая копия → физический оригинал | — |
| `can_access` | Кто имеет доступ к цифровой вещи | — |
| `related_to` | Произвольная связь с меткой | `label` |

**`reason` на ребре `contains`:** `хранение` / `транспорт` / `ремонт` / `покупка`

---

## Люди и группы

```mermaid
graph TD
    Family[Семья]
    Dad[Папа]
    Mom[Мама]
    Son[Сын]
    Daughter[Дочь]
    Grandma[Бабушка]

    Dad -->|part_of| Family
    Mom -->|part_of| Family
    Son -->|part_of| Family
    Daughter -->|part_of| Family
    Grandma -->|part_of| Family
```

- `assigned_to` → конкретный человек: личная ответственность
- `assigned_to` → несколько людей: совместная
- `assigned_to` → Семья: открытая задача, берёт кто свободен

---

## Физическое и цифровое

Физическая вещь отвечает на вопрос **где находится** → `contains`.  
Цифровая вещь отвечает на вопрос **кто имеет доступ** → `can_access`.  
Связь между ними — `represents`.

Поле `kind`: `физическое` / `цифровое` / `смешанное`.

```mermaid
graph TD
    Drawer[Ящик стола]
    CD[CD-диск со снимками\nkind: физическое]
    DocPhysical[Направление от врача\nkind: физическое]

    XrayFiles[Снимки рентгена\nkind: цифровое]
    DocScan[Скан направления\nkind: цифровое]

    ShareDoctor[Подборка для Петрова]
    Doctor[Доктор Петров]

    CD -->|contains| Drawer
    DocPhysical -->|contains| Drawer

    XrayFiles -->|represents| CD
    DocScan -->|represents| DocPhysical

    XrayFiles -->|part_of| ShareDoctor
    DocScan -->|part_of| ShareDoctor
    Doctor -->|can_access| ShareDoctor
```

- Диск физически лежит в ящике, врач его не трогает
- Врач получает `can_access` только к цифровым копиям
- Один физический оригинал может иметь несколько цифровых представлений (скан, фото, PDF)

---

## Доступ и шаринг

`can_access` работает напрямую на конкретные вещи — без глобальных пространств.  
**Каскад:** доступ к вещи автоматически даёт доступ ко всему `part_of` неё вглубь.

```mermaid
graph TD
    Dad[Папа]
    Mom[Мама]
    Alexey[Алексей\nюрпомощник]
    Doctor[Доктор Петров]

    ShareLegal[Подборка для Алексея]
    ShareMed[Снимки для Петрова]

    Case1[Дело о заборе]
    Case3[Дело о земле]
    Xray[Снимки рентгена]
    Mri[МРТ колена]

    PersonalMom[Личные задачи мамы]
    Task1[Записаться к косметологу]
    Task2[Продлить абонемент]

    Case1 -->|part_of| ShareLegal
    Case3 -->|part_of| ShareLegal
    Xray -->|part_of| ShareMed
    Mri -->|part_of| ShareMed
    Task1 -->|part_of| PersonalMom
    Task2 -->|part_of| PersonalMom

    Alexey -->|can_access| ShareLegal
    Doctor -->|can_access| ShareMed
    Mom -->|can_access| PersonalMom
    Dad -->|can_access| Case1
    Dad -->|can_access| Case3
```

**Шаблон доступа** — заранее созданный контейнер с типовым набором.  
Пример: "Доступ врача" — контейнер с нужными цифровыми копиями,  
врачу выдаётся `can_access` к этому контейнеру и ничего лишнего.

---

## Сценарий: периодические платежи

Каждый периодический платёж — шаблон (`thing`) с расписанием.
Каждая оплата — запуск (`run`), `part_of` шаблона.

```mermaid
graph TD
    Dad[Папа]
    Apartment[Квартира]

    Electric[Шаблон: электричество\nperiod: ежемесячно\namount: ~3500р\ndue_day: 10]
    Water[Шаблон: вода\nperiod: ежемесячно\namount: ~1800р\ndue_day: 10]
    Internet[Шаблон: интернет\nperiod: ежемесячно\namount: 600р\ndue_day: 25]
    HOA[Шаблон: УК / кап. ремонт\nperiod: ежемесячно\namount: ~4200р\ndue_day: 20]

    RunElectric[Оплата электричества\nмай 2026\nstatus: выполнено]
    RunWater[Оплата воды\nмай 2026\nstatus: не начато]

    Electric -->|assigned_to| Dad
    Electric -->|about| Apartment
    Water -->|assigned_to| Dad
    Water -->|about| Apartment
    Internet -->|assigned_to| Dad
    HOA -->|assigned_to| Dad
    HOA -->|about| Apartment

    RunElectric -->|part_of| Electric
    RunWater -->|part_of| Water
```

Просроченные платежи — обычный запрос: `paid_until < сегодня`.

---

## Сценарий: юридические обращения

Цепочка обжалований строится через `about` (это обращение обжалует то решение)
и `filed_with` (подано в эту инстанцию).

```mermaid
graph TD
    Dad[Папа]
    Subject[Предмет спора\nнапр. земельный участок]

    LocalAuth[Районная администрация]
    RegionalAuth[Областная администрация]
    Court[Суд первой инстанции]
    AppCourt[Апелляционный суд]

    Case1[Обращение №1\ndeadline: 15 июня\nstatus: выполнено]
    Decision1[Отказ от 20 июня]

    Case2[Обжалование №1\ndeadline: 20 июля\nstatus: выполнено]
    Decision2[Частичный отказ от 5 авг]

    Case3[Исковое заявление\ndeadline: 1 окт\nstatus: в процессе]
    Decision3[Решение суда]

    Case4[Апелляция\nstatus: не начато]

    Case1 -->|assigned_to| Dad
    Case1 -->|about| Subject
    Case1 -->|filed_with| LocalAuth
    Case1 -->|produces| Decision1

    Case2 -->|assigned_to| Dad
    Case2 -->|about| Decision1
    Case2 -->|filed_with| RegionalAuth
    Case2 -->|produces| Decision2

    Case3 -->|assigned_to| Dad
    Case3 -->|about| Decision2
    Case3 -->|filed_with| Court
    Case3 -->|produces| Decision3
    Case3 -->|depends_on| Case2

    Case4 -->|about| Decision3
    Case4 -->|filed_with| AppCourt
    Case4 -->|depends_on| Case3
```

Вся цепочка читается как путь по `about` и `produces`:  
Обращение → решение → следующее обращение → решение → ...

---

## Сценарий: подзадачи

```mermaid
graph TD
    Main[Задача: подготовить мотоцикл к сезону\nstatus: в процессе]

    T1[Купить масло и фильтры\nstatus: выполнено\nassigned_to: Папа]
    T2[Сделать ТО\nstatus: не начато\nassigned_to: Папа]
    T3[Проверить шины\nstatus: не начато\nassigned_to: Семья]
    T4[Помыть мотоцикл\nstatus: не начато\nassigned_to: Сын]

    T1 -->|part_of| Main
    T2 -->|part_of| Main
    T3 -->|part_of| Main
    T4 -->|part_of| Main
    T2 -->|depends_on| T1
```

---

## Сценарий: открытые и личные задачи

```mermaid
graph TD
    Family[Семья]
    Dad[Папа]
    Daughter[Дочь]
    Mom[Мама]

    T1[Задача: долить воду в бочку\nstatus: не начато]
    T2[Задача: убраться на кухне\nstatus: не начато]
    T3[Задача: оплатить воду\ndeadline: 10 июня\nstatus: не начато]

    T1 -->|assigned_to| Family
    T2 -->|assigned_to| Daughter
    T2 -->|assigned_to| Mom
    T3 -->|assigned_to| Dad
```

---

## Уведомления (логика приложения)

| Событие | Кто получает уведомление |
|---------|--------------------------|
| Новая задача `assigned_to` человек | Этот человек |
| Новая задача `assigned_to` Семья | Все члены семьи |
| Задача `depends_on` выполнена | Исполнитель следующей задачи |
| Дедлайн приближается (за 3 дня) | Исполнитель задачи |
| `quantity` = 0 | Все (или исполнитель задачи на покупку) |
| `paid_until` истекает | Исполнитель шаблона платежа |
| Решение по обращению получено (`produces`) | Исполнитель следующего обращения |

---

## SurrealDB: схема

```surql
DEFINE TABLE thing SCHEMALESS;

DEFINE TABLE contains TYPE RELATION FROM thing TO thing SCHEMAFULL;
DEFINE FIELD reason ON contains TYPE option<string>;
DEFINE FIELD since  ON contains TYPE option<datetime>;

DEFINE TABLE part_of    TYPE RELATION FROM thing TO thing;
DEFINE TABLE assigned_to TYPE RELATION FROM thing TO thing;
DEFINE TABLE depends_on  TYPE RELATION FROM thing TO thing;
DEFINE TABLE about       TYPE RELATION FROM thing TO thing;
DEFINE TABLE filed_with  TYPE RELATION FROM thing TO thing;
DEFINE TABLE produces    TYPE RELATION FROM thing TO thing;

DEFINE TABLE needs TYPE RELATION FROM thing TO thing SCHEMAFULL;
DEFINE FIELD quantity ON needs TYPE option<number>;
DEFINE FIELD unit     ON needs TYPE option<string>;

DEFINE TABLE requires TYPE RELATION FROM thing TO thing SCHEMAFULL;
DEFINE FIELD quantity ON requires TYPE option<number>;
DEFINE FIELD unit     ON requires TYPE option<string>;

DEFINE TABLE used TYPE RELATION FROM thing TO thing SCHEMAFULL;
DEFINE FIELD quantity ON used TYPE option<number>;
DEFINE FIELD unit     ON used TYPE option<string>;

DEFINE TABLE represents TYPE RELATION FROM thing TO thing;

DEFINE TABLE can_access TYPE RELATION FROM thing TO thing;

DEFINE TABLE related_to TYPE RELATION FROM thing TO thing SCHEMAFULL;
DEFINE FIELD label ON related_to TYPE string;
```

---

## SurrealQL: примеры запросов

```surql
-- Платежи которые нужно оплатить в этом месяце
SELECT * FROM thing WHERE paid_until < time::now() + 30d
  AND period != NONE;

-- Вся цепочка обжалований по делу (рекурсивно)
SELECT ->about->thing.* FROM thing:case_1 DEPTH 10;

-- Открытые задачи для любого члена семьи
SELECT * FROM thing WHERE status = "не начато"
  AND ->assigned_to->thing CONTAINS thing:family;

-- Мои задачи (личные + семейные, не выполненные)
SELECT * FROM thing WHERE status != "выполнено"
  AND (->assigned_to->thing CONTAINS thing:dad
    OR ->assigned_to->thing CONTAINS thing:family);

-- Задачи без невыполненных зависимостей (можно начать)
SELECT * FROM thing WHERE status = "не начато"
  AND ->depends_on->thing[WHERE status != "выполнено"] IS EMPTY;

-- Все документы/решения по юридическому делу
SELECT ->produces->thing.* FROM thing WHERE ->filed_with->thing != NONE;

-- Просроченные задачи и платежи
SELECT * FROM thing
  WHERE deadline < time::now() AND status NOT IN ["выполнено", "отменено"];
```

---

## YAML: описание схемы

```yaml
узел:
  тип: thing
  поля:
    обязательные:
      - название: текст
    необязательные:
      - описание: текст
      - количество: число
      - единица: текст
      - куплено: дата
      - цена: число
      - заметки: текст
      - статус: текст         # не начато / в процессе / выполнено / ожидает / отменено
      - дедлайн: дата
      - приоритет: текст      # низкий / средний / высокий
      - роль: текст           # папа / мама / сын / дочь / бабушка
      - сумма: число          # для платежей
      - период: текст         # ежемесячно / ежеквартально / ежегодно
      - день_оплаты: число    # число месяца: 1–31
      - оплачено_до: дата     # для периодических платежей
    дополнительные: любые

связи:
  contains:
    от: thing
    к: thing
    поля:
      - reason: текст         # хранение / транспорт / ремонт / покупка
      - since: дата
  part_of:
    описание: часть чего / подзадача / запуск шаблона
    от: thing
    к: thing
  assigned_to:
    описание: кто отвечает (человек, несколько людей или вся семья)
    от: thing
    к: thing
  depends_on:
    описание: задача ждёт выполнения другой
    от: thing
    к: thing
  about:
    описание: задача/обращение касается этой вещи или обжалует это решение
    от: thing
    к: thing
  filed_with:
    описание: обращение подано в эту инстанцию/организацию
    от: thing
    к: thing
  needs:
    описание: нужно купить
    от: thing
    к: thing
    поля:
      - quantity: число
      - unit: текст
  requires:
    описание: плановый расход (шаблон → ингредиент/деталь)
    от: thing
    к: thing
    поля:
      - quantity: число
      - unit: текст
  produces:
    описание: результат выполнения (решение, документ, блюдо, изделие)
    от: thing
    к: thing
  used:
    описание: фактический расход при запуске
    от: thing
    к: thing
    поля:
      - quantity: число
      - unit: текст
  represents:
    описание: цифровая копия → физический оригинал
    от: thing   # цифровое
    к: thing    # физическое

  can_access:
    описание: кто имеет доступ к цифровой вещи или контейнеру
    от: thing   # человек или группа
    к: thing    # цифровая вещь или контейнер

  related_to:
    описание: произвольная связь
    от: thing
    к: thing
    поля:
      - label: текст
```

---

## Сценарий: жалоба с fan-out по инстанциям

Одна жалоба охватывает несколько объектов. Вышестоящая инстанция пересылает её вниз —
каждое подзадело живёт независимо, но остаётся связано с корнем через `part_of`.

```mermaid
graph TD
    Root[Жалоба в облпрокуратуру\nstatus: выполнено]
    RegProc[Областная прокуратура]
    Notify[Уведомление о пересылке]

    Root -->|filed_with| RegProc
    Root -->|about| School1[Школа №1]
    Root -->|about| School2[Школа №2]
    Root -->|about| School10[Школа №10 ...]
    Root -->|produces| Notify

    Sub1[Дело: школа №1\nstatus: в процессе]
    Sub2[Дело: школа №2\nstatus: выполнено]
    Sub10[Дело: школа №10\nstatus: не начато]

    Sub1 -->|part_of| Root
    Sub2 -->|part_of| Root
    Sub10 -->|part_of| Root

    Sub1 -->|filed_with| Proc1[Прокуратура района 1]
    Sub1 -->|about| School1
    Sub1 -->|produces| Result1[Результат проверки №1\nнарушения выявлены]

    Sub2 -->|filed_with| Proc2[Прокуратура района 2]
    Sub2 -->|about| School2
    Sub2 -->|produces| Result2[Результат проверки №2\nнарушений не выявлено]

    Appeal2[Обжалование по школе №2\nstatus: не начато]
    Appeal2 -->|about| Result2
    Appeal2 -->|filed_with| RegProc
```

**Почему это работает без изменений схемы:**
- `part_of` связывает подзадела с корневой жалобой — всегда виден источник
- Каждое подзадело независимо: своя прокуратура (`filed_with`), свой результат (`produces`), своё обжалование (`about`)
- Fan-out естественен для графа — у одного узла может быть сколько угодно рёбер любого типа

```surql
-- Все подзадела и их статусы
SELECT name, status, ->filed_with->thing.name AS прокуратура
FROM thing WHERE ->part_of->thing = thing:root_complaint;

-- Результаты которые можно обжаловать (есть результат, нет обжалования)
SELECT * FROM thing WHERE ->part_of->thing = thing:root_complaint
  AND ->produces->thing != NONE
  AND NOT (SELECT * FROM thing WHERE ->about->thing = (->produces->thing));

-- Вся цепочка от корневой жалобы вглубь
SELECT ->part_of<-thing.* FROM thing:root_complaint DEPTH 5;
```

---

## Сценарий: медицина — приёмы, назначения, направления

Врач `part_of` больница. Приём — задача с дедлайном. Назначения и направления —
`produces` из приёма. Следующий приём `about` направление.

```mermaid
graph TD
    Patient[Папа]
    HospA[Городская поликлиника]
    HospB[Областной центр]
    Doctor[Врач Иванов]

    Visit1[Приём у Иванова\nstatus: выполнено]
    Prescription[Назначение: курс лечения]
    Referral[Направление в областной центр]

    Visit2[Приём в областном центре\ndeadline: до 1 июля\nstatus: ожидает]

    SelfReg[Записаться самим онлайн\nstatus: выполнено]
    Queue[Встать в очередь у дежурного\nstatus: выполнено]
    Callback[Ждём звонка от дежурного\ndeadline: 21 мая\nstatus: ожидает]
    Followup[Позвонить дежурному самим\ndeadline: 22 мая\nstatus: не начато]

    Doctor -->|part_of| HospA
    Visit1 -->|filed_with| HospA
    Visit1 -->|about| Doctor
    Visit1 -->|about| Patient
    Visit1 -->|produces| Prescription
    Visit1 -->|produces| Referral
    Visit1 -->|assigned_to| Patient

    Visit2 -->|about| Referral
    Visit2 -->|filed_with| HospB
    Visit2 -->|about| Patient
    Visit2 -->|assigned_to| Patient

    SelfReg -->|about| Visit2
    Queue -->|about| Visit2
    Callback -->|depends_on| Queue
    Followup -->|depends_on| Callback
```

**Таймаут на звонок:** `Followup` с дедлайном на следующий день после `Callback` —
страховка от забывчивости. Уведомление сработает когда дедлайн `Callback` истечёт
без выполнения.

**OR-логика записи:** два пути к одному приёму (самостоятельно или через дежурного) —
это поведение приложения. Когда хотя бы один путь сработал, `Visit2` помечается
подтверждённым. В схеме не формализуется.

```surql
-- Все предстоящие приёмы у врачей
SELECT * FROM thing WHERE ->filed_with->thing.name CONTAINS "больниц"
  AND deadline > time::now() AND status != "выполнено";

-- Назначения и направления из последнего приёма
SELECT ->produces->thing.* FROM thing:visit_ivanov_may;

-- Незакрытые задачи по ожиданию обратного звонка
SELECT * FROM thing WHERE name CONTAINS "звонк" AND status = "ожидает"
  AND deadline < time::now() + 1d;

-- Все приёмы конкретного пациента
SELECT <-about<-thing[WHERE ->filed_with->thing != NONE].* FROM thing:dad;
```

---

## Открытые вопросы

- [ ] История перемещений вещей?
- [ ] Повторяющиеся задачи — шаблон с расписанием (каждую субботу, каждые 10000 км)?
- [ ] Уведомления — push или только в приложении?
- [ ] Фотографии вещей?
- [ ] Штрихкоды / QR-коды при добавлении?
- [ ] Документы по юридическим делам — хранить файлы или только ссылки?

# Renovation Estimator — MVP Design

Дата: 2026-06-11 · Версия: 1.1 (scope урезан до минимума)
Статус: утверждён; базовый MVP реализован

Примечание реализации: backend photo API завершён, но текущий frontend только
валидирует выбранные фото и ещё не отправляет их на сервер. Остальные известные
ограничения перечислены в `../../../PROJECT.md`.

## 1. Видение

Веб-сервис для быстрого расчёта строительной сметы по отделочным работам.
Пользователь загружает фото объекта, вводит размеры комнат, выбирает работы —
шпаклёвка, грунтовка, покраска — и получает смету с разбивкой по работам и
материалам, печатью из браузера и ссылкой для отправки клиенту.

Ключевые решения MVP:

- **Фото** — только документация объекта, в расчёте не участвует.
- **Цены** — сид-прайс в БД из `data/price_list.seed.json`; в конкретной смете
  пользователь правит цену работы инлайн. Редактирование самого справочника — Phase 2.
- **Без регистрации** — анонимные сметы, доступ по криптослучайной share-ссылке.
- **Языки** — русский и французский; валюта — EUR.
- **Стек** — React (Vite, TypeScript) + FastAPI (Python) + SQLite (`create_all` + сид, без миграций).
- **Печать** — через браузер (print-CSS), без серверного PDF.

## 2. Структура экранов (4)

| # | Экран | Маршрут | Содержание |
|---|-------|---------|------------|
| 1 | Главная | `/` | Список последних смет (id в localStorage), кнопка «Новая смета» |
| 2 | Мастер · шаг 1 «Объект» | `/estimate/new` | Название, адрес (опц.), загрузка фото (drag&drop) |
| 3 | Мастер · шаг 2 «Комнаты и работы» | `/estimate/:id/rooms` | Размеры, окна/двери, выбор работ; «+ добавить комнату» |
| 4 | Смета | `/estimate/:id` | Таблица позиций, инлайн-правка цены работы, итог с TVA/НДС, кнопки «Печать» и «Поделиться» |
| — | Просмотр по ссылке | `/s/:share_token` | Экран 4 в режиме read-only |

В шапке: переключатель языка RU/FR.

## 3. Пользовательский сценарий (основной)

1. «Новая смета» → название объекта, адрес (опц.), 1–3 фото. → «Далее».
2. Размеры комнаты 4 × 3 × 2.7, окно 1.5 × 1.4, дверь 0.9 × 2.05.
   Работы: шпаклёвка (2 слоя), грунтовка (1), покраска (2). → «Рассчитать».
3. Смета: по работе — площадь, цена/м², сумма; по материалу — упаковки, сумма.
   Правка цены покраски инлайн → итог пересчитывается (повторный `/calculate`).
4. «Печать» (диалог печати браузера → бумага или PDF) и/или share-ссылка клиенту.
5. Клиент открывает `/s/<token>` — та же смета, read-only.

Альтернативные ветки: несколько комнат («+ добавить комнату», смета группируется
по комнатам); возврат позже через список на главной; ошибка валидации —
подсветка поля, сообщение на языке UI.

## 4. Поля форм и валидация

### Шаг 1 — объект

| Поле | Тип | Правила |
|------|-----|---------|
| title | text | обязательное, 1–120 символов |
| address | text | опциональное, ≤ 250 |
| photos[] | file | jpeg/png/webp; ≤ 10 МБ каждое; ≤ 10 шт. |

### Шаг 2 — комната

| Поле | Тип | Default | Правила |
|------|-----|---------|---------|
| name | text | «Комната N» | ≤ 80 |
| length_m | number | — | 0.5–50, шаг 0.01 |
| width_m | number | — | 0.5–50 |
| height_m | number | 2.7 | 1.5–10 |
| include_ceiling | checkbox | true | потолок входит в расчёт |
| окна[]: width_m, height_m, count | number | 1.5 × 1.4 × 1 | 0.1–10 м; count 1–20 |
| двери[]: width_m, height_m, count | number | 0.9 × 2.05 × 1 | то же |

### Шаг 2 — работы (для каждой отмеченной)

| Поле | Тип | Default | Правила |
|------|-----|---------|---------|
| выбрана | checkbox | off | хотя бы одна работа на комнату |
| layers | number | шпаклёвка 2 · грунтовка 1 · покраска 2 | 1–5 |
| unit_price (€/м²) | number | из прайса | 0–1000, редактируемое |

Нормы расхода, фасовка и цена материала берутся из прайса снапшотом и в форме
не редактируются (Phase 2).

### Итоговый блок

| Поле | Default | Правила |
|------|---------|---------|
| vat_pct (TVA/НДС, %) | 20 | 0–30 |

## 5. Формулы расчёта

Для каждой комнаты:

```
P           = 2 × (L + W)                              # периметр, м
S_проёмов   = Σ (w × h × count)                        # окна + двери, м²
S_стен      = max(0, P × H − S_проёмов)                # м²
S_потолка   = L × W   (если include_ceiling, иначе 0)
S_базовая   = S_стен + S_потолка
```

Для каждой выбранной работы в комнате:

```
labor_cost      = S_базовая × unit_price × layers
consumption     = S_базовая × consumption_per_m2 × layers   # л или кг
packages        = ceil(consumption / package_size)          # целые упаковки
material_cost   = packages × package_price
```

Итоги сметы:

```
subtotal = Σ (labor_cost + material_cost)  по всем работам всех комнат
total    = subtotal × (1 + vat_pct/100)
```

Округление: площади и расход — до 0.01; деньги — до 0.01 € (HALF_UP) на уровне позиции.

Дефолтные нормы расхода (сид): грунтовка 0.12 л/м²; шпаклёвка 1.2 кг/м²/слой;
краска 0.15 л/м²/слой.

Контрольный пример: комната 4 × 3 × 2.7, окно 1.5 × 1.4, дверь 0.9 × 2.05 →
P = 14; S_проёмов = 3.945; S_стен = 33.86; S_потолка = 12; S_базовая = 45.86 м².

Единый модуль расчёта живёт на backend; frontend показывает результат
`/calculate` и не дублирует формулы.

## 6. Структура базы данных (SQLite)

```
estimates
  id            TEXT PK (uuid4)
  title         TEXT NOT NULL
  address       TEXT
  locale        TEXT CHECK(ru|fr) DEFAULT 'ru'
  currency      TEXT DEFAULT 'EUR'
  vat_pct       REAL DEFAULT 20
  share_token   TEXT UNIQUE NOT NULL      -- secrets.token_urlsafe(16+)
  total_amount  REAL                      -- кэш последнего расчёта
  created_at, updated_at  DATETIME

rooms
  id, estimate_id FK→estimates(CASCADE)
  name TEXT, length_m REAL, width_m REAL, height_m REAL
  include_ceiling INTEGER DEFAULT 1

openings
  id, room_id FK→rooms(CASCADE)
  kind TEXT CHECK(window|door)
  width_m REAL, height_m REAL, count INTEGER DEFAULT 1

work_types                                -- справочник (read-only в MVP)
  id, code TEXT UNIQUE CHECK(putty|primer|paint)
  name_ru TEXT, name_fr TEXT
  unit TEXT DEFAULT 'm2'
  base_unit_price REAL                    -- €/м²
  default_layers INTEGER

materials                                 -- справочник, 1:1 c work_type
  id, work_type_id FK→work_types
  name_ru TEXT, name_fr TEXT
  consumption_per_m2 REAL
  consumption_unit TEXT CHECK(l|kg)
  package_size REAL, package_price REAL

room_works                                -- выбранная работа + снапшоты цен
  id, room_id FK→rooms(CASCADE), work_type_id FK→work_types
  layers INTEGER
  unit_price REAL                         -- снапшот/override
  material_consumption_per_m2 REAL        -- снапшоты из справочника
  material_package_size REAL
  material_package_price REAL
  computed_area REAL, labor_cost REAL, material_cost REAL
  UNIQUE(room_id, work_type_id)

photos
  id, estimate_id FK→estimates(CASCADE)
  file_path TEXT, original_name TEXT, mime TEXT, size_bytes INTEGER
  created_at DATETIME
```

Принцип снапшотов: при выборе работы цены копируются из справочника в
`room_works`; будущая правка прайса не меняет уже созданные сметы.

## 7. API (REST, FastAPI)

| Метод и путь | Назначение |
|--------------|-----------|
| `POST /api/estimates` | создать смету (title, address, locale) |
| `GET /api/estimates/{id}` | смета целиком (комнаты, работы, фото, итоги) |
| `PUT /api/estimates/{id}` | обновить шапку (title, address, vat_pct, locale) |
| `DELETE /api/estimates/{id}` | удалить смету и файлы фото |
| `GET /api/shared/{share_token}` | read-only смета для клиента |
| `POST /api/estimates/{id}/rooms` · `PUT/DELETE /api/rooms/{id}` | комнаты (openings и works вложенным JSON) |
| `POST /api/estimates/{id}/photos` (multipart) · `DELETE /api/photos/{id}` | фото |
| `POST /api/estimates/{id}/calculate` | пересчёт: возвращает и сохраняет computed-поля |
| `GET /api/price-list` | справочник для префилла формы (read-only) |

Ошибки: конверт `{ "error": { "code", "message" } }`, тексты локализует frontend.

## 8. i18n

Словари `ru.json` / `fr.json` во frontend; переключатель в шапке (localStorage +
`estimates.locale`). Названия работ/материалов — `name_ru` / `name_fr` из БД.
Печатная версия — на языке текущего UI.

## 9. Хранение файлов

Фото — `data/uploads/{estimate_id}/`, uuid-имена; в БД только метаданные.
`data/uploads/` и `data/app.db` — в `.gitignore`.

## 10. Обработка ошибок

- Валидация на границе (Pydantic) — 422 с кодом поля.
- Проёмы больше площади стен → S_стен = 0, расчёт продолжается, warning в ответе.
- Несуществующий id/token → 404. Превышение лимитов фото → 413/422.

## 11. Тестирование

- Unit модуля расчёта: контрольный пример §5; проёмы > стен; потолок выключен;
  ceil упаковок; округление денег; сумма по нескольким комнатам; VAT.
- API-тесты: CRUD сметы, calculate, share-token (read-only), лимиты фото.
- Acceptance: сценарий §3 от создания до печати/share.

## 12. Перенесено в Phase 2 (осознанно вырезано из MVP)

| Что | Почему вырезано |
|-----|-----------------|
| Серверный PDF (weasyprint) | печать браузера с print-CSS закрывает потребность v1 |
| Экран прайс-листа + `PUT /api/price-list` | цена правится инлайн в смете; справочник в v1 read-only |
| Alembic-миграции | для SQLite-прототипа достаточно `create_all` + сид |
| HEIC-фото | нужна конвертация на сервере; jpeg/png/webp достаточно |
| `status` (draft/final), `markup_pct` | поля «на вырост», в сценарии v1 не используются |
| Правка норм расхода/фасовки в форме | перегружает шаг 2; в v1 редактируются только слои и цена работы |
| AI-анализ фото (промпты в `prompts/`) | отдельная фича с API-бюджетом |
| Excel-экспорт, регистрация, мультивалютность, региональные прайсы, PWA | классический пост-MVP |

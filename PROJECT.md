# Renovation Estimator

Веб-сервис расчёта строительной сметы по отделочным работам: пользователь
загружает фото объекта, вводит размеры комнат, выбирает работы (шпаклёвка,
грунтовка, покраска) и получает смету с разбивкой работ и материалов,
браузерной печатью и share-ссылкой.

## Статус

MVP реализован локально. По состоянию на 11 июня 2026 года:

- backend: FastAPI, SQLAlchemy, SQLite (`create_all`), seed прайса, расчёт,
  REST API и фото-хранилище;
- frontend: React/Vite/TypeScript, мастер, экран сметы, share-view, RU/FR и
  print-CSS;
- проверки: 17 backend-тестов, frontend typecheck и production build проходят.

Известное ограничение текущего UI: backend поддерживает upload/delete фото,
но шаг 1 frontend пока только валидирует выбранные файлы и не отправляет их.
Share-view использует сохранённые суммы, но не получает отдельный результат
`/calculate`, поэтому расход и число упаковок в нём отображаются прочерками.

## Scope MVP

- Мастер из 2 шагов: объект + фото (jpeg/png/webp) → комнаты, проёмы, работы.
- Несколько комнат в одной смете.
- Расчёт работ и материалов по сид-прайсу; цена работы правится инлайн в смете
  (снапшоты цен — правка прайса не меняет старые сметы).
- Итог с TVA/НДС (%).
- Печать сметы из браузера (print-CSS), read-only ссылка для клиента.
- Языки RU/FR, валюта EUR, без регистрации.

## Реализованный API

- CRUD смет: `POST/GET/PUT/DELETE /api/estimates...`.
- Комнаты: `POST /api/estimates/{id}/rooms`, `PUT/DELETE /api/rooms/{id}`.
- Расчёт: `POST /api/estimates/{id}/calculate`.
- Фото: `POST /api/estimates/{id}/photos`, `DELETE /api/photos/{id}`.
- Share-view: `GET /api/shared/{share_token}`.
- Read-only прайс: `GET /api/price-list`.

## Стек

React 19 (Vite 7, TypeScript) · FastAPI (Python 3.12+) · SQLAlchemy 2 ·
SQLite (`create_all` + seed, без миграций).

## Локальный запуск

Backend:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn backend.app.main:app --reload
```

Frontend, в отдельном терминале:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`; OpenAPI: `http://127.0.0.1:8000/docs`.
Vite проксирует `/api` на backend.

Проверки:

```bash
pytest -q
cd frontend && npm run typecheck && npm run build
```

## Структура

```
├── PROJECT.md       # этот файл
├── docs/            # дизайн, ТЗ, ADR
├── frontend/        # React-приложение
├── backend/         # FastAPI
├── prompts/         # промпты AI-фич (фаза 2)
├── data/            # сид прайса, БД, загрузки (uploads вне git)
└── tests/           # тесты backend (pytest)
```

## Roadmap

- **Фаза 1 (MVP)** — основной scope реализован; frontend-загрузка фото и
  детализация расхода/упаковок в share-view остаются известными ограничениями
  (закрываются в Phase 1.1).
- **Фаза 1.1 (профессиональный каталог)** — спроектирована, код не начат.
  Дизайн: `docs/superpowers/specs/2026-06-11-phase-1.1-pro-catalog-design.md`,
  черновик прайса: `data/price_list.seed.v2.json`. Scope: 8 работ полного
  малярного цикла (трещины, армирование, старт/финиш шпаклёвка, шлифовка,
  грунтовка, акрил, покраска 1–3 слоя), единица м.п., штучные материалы,
  разделы devis с итогами HT/TVA/TTC, пресеты TVA 10 %/20 %, долги MVP
  (фото-upload в UI, расход в share-view).
- **Фаза 2** — реквизиты devis (SIRET, номер, срок действия, mentions légales),
  раздельные цены стены/потолок, доп. работы (dépose papier peint, bâchage,
  plinthes, déplacement, forfait), серверный PDF, экран редактирования
  прайс-листа, Alembic-миграции, HEIC-фото, markup_pct и статусы смет, правка
  норм расхода в форме, AI-анализ фото.
- **Фаза 3** — Excel-экспорт, регистрация и список смет, региональные прайсы,
  мультивалютность, PWA, шаблоны смет, каталоги материалов.

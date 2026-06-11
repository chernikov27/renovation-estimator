# Renovation Estimator

Веб-сервис расчёта строительной сметы: фото объекта + размеры комнат + выбор
работ (шпаклёвка, грунтовка, покраска) → смета с материалами, браузерной
печатью и share-ссылкой.

## Status

MVP реализован. Backend, frontend, REST API и автоматические backend-тесты
находятся в этом репозитории. Актуальный scope и ограничения: `PROJECT.md`.

## Stack

React 19 · Vite 7 · TypeScript · FastAPI · Python 3.12+ · SQLAlchemy 2 ·
SQLite без Alembic. EUR, RU/FR.

## Getting started

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn backend.app.main:app --reload
```

В другом терминале:

```bash
cd frontend
npm install
npm run dev
```

- UI: `http://127.0.0.1:5173`
- OpenAPI: `http://127.0.0.1:8000/docs`

Проверки:

```bash
pytest -q
cd frontend && npm run typecheck && npm run build
```

Фото API реализован, но текущий frontend ещё не отправляет выбранные на первом
шаге файлы. В share-view сохранённые суммы доступны, но расход и упаковки
показываются прочерками. Серверного PDF нет: используется печать браузера.

## Layout

```
.
├── AGENTS.md        # Codex rules (inherits ../AGENTS.md)
├── CLAUDE.md        # Claude rules (inherits ../CLAUDE.md)
├── README.md        # this file
├── PROJECT.md       # видение, scope MVP, roadmap
├── .env.example     # required env vars, with safe placeholders
├── .gitignore
├── docs/            # дизайн-док, ТЗ для Codex, ADR
├── frontend/        # React-приложение
├── backend/         # FastAPI
├── prompts/         # промпты AI-фич (фаза 2)
├── data/            # сид прайса, SQLite, uploads (вне git)
└── tests/           # тесты backend (pytest)
```

## Workflow

This project follows the shared process in `../WORKFLOW.md` and the rulebook in `../RULES.md`.

- Claude rules: `./CLAUDE.md` (inherits `../CLAUDE.md`)
- Codex rules: `./AGENTS.md` (inherits `../AGENTS.md`)

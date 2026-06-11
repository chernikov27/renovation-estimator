# Renovation Estimator

Веб-сервис расчёта строительной сметы: фото объекта + размеры комнат + выбор
работ (шпаклёвка, грунтовка, покраска) → смета с PDF и share-ссылкой.

## Status

Прототип: проектирование завершено, код не написан. См. `PROJECT.md`.

## Stack

React (Vite, TypeScript) · FastAPI (Python 3.12+) · SQLite + Alembic. EUR, RU/FR.

## Getting started

```bash
cp .env.example .env
# реализация ещё не начата — см. docs/CODEX_REQUIREMENTS.md
```

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

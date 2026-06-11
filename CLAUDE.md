# Claude — Project Instructions

Inherits the global Claude rules from `../CLAUDE.md`, the shared process in `../WORKFLOW.md`, and the rulebook in `../RULES.md`.
Use this file only for project-specific overrides and Claude memory.

## What this project does

Веб-сервис расчёта строительной сметы: фото + размеры комнат + работы
(шпаклёвка, грунтовка, покраска) → смета, PDF, share-ссылка. RU/FR, EUR.

## Stack

React (Vite, TypeScript) в `frontend/` · FastAPI (Python 3.12+, SQLAlchemy,
Alembic) в `backend/` · SQLite в `data/app.db`.

## Entry points

- Дизайн: `docs/superpowers/specs/2026-06-11-renovation-estimator-mvp-design.md`
- ТЗ: `docs/CODEX_REQUIREMENTS.md`
- Сид прайса: `data/price_list.seed.json`

## API / Agent surface

REST `/api/...` — см. раздел 7 дизайн-дока. Read-only доступ по `share_token`.

## Commands

Реализация не начата; команды появятся вместе со скелетом frontend/backend.

## Environment

`.env` из `.env.example`. Без секретов в коде.

## Security-critical paths

- Загрузка фото: проверка MIME + magic bytes, лимиты 10 МБ / 10 шт.
- `share_token`: `secrets.token_urlsafe(16)`+, по токену только чтение.
- Валидация всех входных данных через Pydantic на границе API.

## Production notes

MVP без авторизации — не публиковать с чувствительными данными.

## Overrides

Формулы расчёта живут только на backend; frontend не дублирует расчёт.

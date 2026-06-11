# backend/

FastAPI-приложение на Python 3.12+, SQLAlchemy 2 и SQLite. Схема создаётся
через `create_all`, прайс загружается из `../data/price_list.seed.v2.json`.
Alembic и серверный PDF в MVP не используются.

## Запуск

Из корня проекта в Python 3.12 venv:

```bash
python -m pip install -e '.[dev]'
uvicorn backend.app.main:app --reload
```

OpenAPI доступен на `http://127.0.0.1:8000/docs`.

## Состав

- `app/calculation.py` — чистые функции расчёта без I/O.
- `app/models.py` — SQLAlchemy-модели.
- `app/api.py` — CRUD смет/комнат, calculate, share, прайс и фото.
- `app/seed.py` — идемпотентный seed прайса.

Фото сохраняются в `data/uploads/{estimate_id}/`. Разрешены JPEG/PNG/WebP,
до 10 МБ и до 10 файлов на смету; проверяются MIME и magic bytes.

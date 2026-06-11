# Next-step prompt для Codex

Скопировать как первое сообщение Codex:

---

Реализуй MVP по `docs/CODEX_REQUIREMENTS.md` (дизайн — `docs/superpowers/specs/2026-06-11-renovation-estimator-mvp-design.md`, схема БД §6, API §7, формулы §5).

Порядок:
1. Backend-скелет в `backend/`: FastAPI + SQLAlchemy + SQLite (`create_all`), сид из `data/price_list.seed.json`.
2. Модуль расчёта чистыми функциями + unit-тесты в `tests/` (контрольный пример: комната 4×3×2.7, окно 1.5×1.4, дверь 0.9×2.05 → S_базовая = 45.86 м²). Сначала тесты, потом код.
3. REST API из §7 + API-тесты.
4. Frontend в `frontend/` (React + Vite + TS): главная, мастер из 2 шагов, смета с инлайн-правкой цены, share-view read-only, i18n ru/fr, print-CSS.

Жёсткие рамки: без авторизации; без серверного PDF (печать браузера); формулы только на backend; снапшоты цен в `room_works`; фото jpeg/png/webp ≤10 МБ ≤10 шт. с проверкой magic bytes. Вне scope (§6 ТЗ): Alembic, экран прайс-листа, HEIC, markup/status, AI, Excel.

Останавливайся после каждого из 4 шагов и показывай, что тесты зелёные.

# data/

- `price_list.seed.json` — сид прайса (работы и материалы, RU/FR, EUR).
  Загружается в БД при первом запуске backend.
- `price_list.seed.v2.json` — черновик прайса Phase 1.1 (8 работ, группы,
  единица м.п., TVA-пресеты). Backend его пока НЕ читает — см. миграционный
  план в `../docs/superpowers/specs/2026-06-11-phase-1.1-pro-catalog-design.md`.
- `app.db` — файл SQLite (создаётся при запуске, вне git).
- `uploads/{estimate_id}/` — фото объектов с UUID-именами (вне git).
  Метаданные хранятся в SQLite; разрешены JPEG/PNG/WebP до 10 МБ и до 10 фото
  на смету.

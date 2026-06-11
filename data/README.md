# data/

- `price_list.seed.json` — сид прайса (работы и материалы, RU/FR, EUR).
  Сохранён для legacy/MVP-совместимости.
- `price_list.seed.v2.json` — основной импорт Phase 1.1: группы, расширенные
  единицы, quantity basis и пресеты TVA.
- `app.db` — файл SQLite (создаётся при запуске, вне git).
- `uploads/{estimate_id}/` — фото объектов с UUID-именами (вне git).
  Метаданные хранятся в SQLite; разрешены JPEG/PNG/WebP до 10 МБ и до 10 фото
  на смету.

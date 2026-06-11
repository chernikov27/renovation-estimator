# tests/

Backend-тесты запускаются из корня проекта в Python 3.12 venv:

```bash
pytest -q
```

- `unit/test_calculation.py` — площади, округление, упаковки, TVA и несколько
  комнат.
- `integration/test_seed.py` — идемпотентность seed прайса.
- `api/test_estimates_api.py` — CRUD, комнаты, calculate, share, стабильные
  ошибки, снапшоты цен и ограничения фото.

Текущий набор: 17 тестов.

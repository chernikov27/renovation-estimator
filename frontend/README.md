# frontend/

React-приложение (Vite + TypeScript) для MVP сметчика ремонта.

Экраны: главная, мастер (объект → комнаты и работы), смета,
read-only просмотр по share-ссылке. i18n: ru/fr.

Локально frontend ожидает backend API на `http://127.0.0.1:8000`.

## Запуск

```bash
npm install
npm run dev
```

UI: `http://127.0.0.1:5173`. Vite проксирует `/api` на backend.

```bash
npm run typecheck
npm run build
```

## Маршруты

- `/` — последние локальные сметы.
- `/estimate/new` — объект и выбор фото.
- `/estimate/:id/rooms` — комнаты, проёмы и работы.
- `/estimate/:id` — расчёт, материалы, цены, печать и share-ссылка.
- `/s/:shareToken` — read-only просмотр.

## Ограничение

Выбор файлов на шаге объекта валидирует тип, размер и количество, но upload в
backend пока не вызывается. Backend photo API реализован отдельно. Share-view
показывает сохранённые суммы, но расход и число упаковок без вызова calculate
отображаются прочерками.

# Phase 1.1 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing React frontend to consume the Phase 1.1 catalog, render grouped professional works, support area- and length-based quantities, expose TVA 10%/20% presets, and keep legacy MVP estimates and catalogs usable.

**Architecture:** Add a small catalog normalization layer between `api.ts` and the UI. It requests `GET /api/price-list?version=2`, converts both v2 and legacy v1 payloads into one frontend model, and centralizes work-state/payload rules. Existing routes remain unchanged; the room form and estimate table become group-aware while preserving legacy works with area semantics.

**Tech Stack:** React 19, TypeScript 5.9, Vite 7, React Router 7, Vitest for pure frontend unit tests, existing RU/FR dictionary i18n.

---

## Product Decisions

- New room entry requests `GET /api/price-list?version=2`.
- If an older backend ignores `version=2` and returns the v1 shape, the frontend normalizes it and keeps the original three-work flow.
- Existing estimates containing `putty`, `primer`, or `paint` remain readable and editable.
- V2 groups are ordered by `group.sort_order`; works are ordered by group and `work.sort_order`.
- Area works use the backend-computed room area and do not send `quantity`.
- Length works show a numeric `quantity` field and send it in room payloads.
- `acrylic` starts with the current room perimeter `2 × (length + width)`; it updates while untouched, then preserves a user override.
- `crack_treatment` starts unselected with an empty length so an unknown measurement never blocks the normal room flow.
- Other active v2 works remain selected by default, matching the current MVP behavior where catalog works start selected.
- TVA defaults to 20%. The create flow exposes 10% and 20% as a segmented control. The owner estimate view also exposes these presets and recalculates after a change. Read-only share view displays the saved TVA only.
- No backend changes are part of this plan.

## File Map

**Create**

- `frontend/src/catalog.ts` — catalog normalization, grouping, initial work-state, perimeter default, and room-work payload helpers.
- `frontend/src/catalog.test.ts` — pure unit tests for v1 fallback, v2 ordering, area/length quantities, and legacy compatibility.
- `frontend/vitest.config.ts` — Node-based Vitest configuration for pure TypeScript tests.

**Modify**

- `frontend/src/api.ts` — v2 catalog types, quantity/unit fields, and `getPriceListV2()`.
- `frontend/src/ui/RoomsPage.tsx` — grouped work sections and length inputs.
- `frontend/src/ui/NewEstimatePage.tsx` — TVA 10/20 segmented control and selected value in create payload.
- `frontend/src/ui/EstimateView.tsx` — grouped estimate lines, quantity/unit display, preservation of length quantity during price updates, owner TVA presets.
- `frontend/src/i18n.tsx` — RU/FR labels for groups, quantity, units, TVA presets, and validation.
- `frontend/src/styles.css` — group layout, stable work-row columns, TVA segmented control, responsive and print styles.
- `frontend/package.json` — `test` script and Vitest dev dependency.
- `frontend/package-lock.json` — lockfile update.
- `frontend/README.md` — Phase 1.1 catalog behavior and verification commands.

## Task 1: Define and Normalize Catalog Contracts

**Files:**
- Create: `frontend/src/catalog.ts`
- Create: `frontend/src/catalog.test.ts`
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/src/api.ts:14-58,85-123,154-179`
- Modify: `frontend/package.json:6-23`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Add Vitest and the test script**

Add `vitest` as a dev dependency and this script:

```json
"test": "vitest run"
```

Use a Node environment because catalog tests do not require the DOM:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node"
  }
});
```

- [ ] **Step 2: Write failing tests for v2 and legacy normalization**

Cover these exact behaviors in `catalog.test.ts`:

```ts
it("orders v2 groups and active works by sort_order", () => {
  const catalog = normalizePriceList(v2Payload);
  expect(catalog.groups.map((group) => group.code)).toEqual(["prep", "enduits", "peinture"]);
  expect(catalog.groups[0].works.map((work) => work.code)).toEqual([
    "crack_treatment",
    "mesh_reinforcement"
  ]);
});

it("normalizes the legacy response without changing its three works", () => {
  const catalog = normalizePriceList(v1Payload);
  expect(catalog.version).toBe(1);
  expect(catalog.groups.flatMap((group) => group.works).map((work) => work.code)).toEqual([
    "paint",
    "primer",
    "putty"
  ]);
  expect(catalog.groups[0].works.every((work) => work.quantity_basis === "area")).toBe(true);
});
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
cd frontend && npm test
```

Expected: FAIL because `normalizePriceList` and the unified catalog types do not exist.

- [ ] **Step 4: Extend API types without removing legacy types**

Define these frontend contracts in `api.ts`:

```ts
export type WorkUnit = "m2" | "ml" | "u";
export type QuantityBasis = "area" | "length";
export type MaterialUnit = "l" | "kg" | "u" | "m2";

export type WorkGroup = {
  code: string;
  sort_order: number;
  name_ru: string;
  name_fr: string;
};

export type ProfessionalWorkType = {
  id: string;
  code: string;
  group: string;
  sort_order: number;
  name_ru: string;
  name_fr: string;
  unit: WorkUnit;
  quantity_basis: QuantityBasis;
  base_unit_price: number;
  default_layers: number;
  max_layers: number;
  active: boolean;
  material: {
    name_ru: string;
    name_fr: string;
    consumption_per_unit: number;
    consumption_unit: MaterialUnit;
    package_size: number;
    package_price: number;
  };
};

export type ProfessionalPriceList = {
  version: 2;
  currency: string;
  vat_presets: number[];
  groups: WorkGroup[];
  work_types: ProfessionalWorkType[];
};
```

Keep the existing `PriceList` as the v1 contract. Add `quantity?: number` to `RoomWorkPayload`; add `group`, `unit`, `quantity_basis`, and `quantity` to `RoomWork`; add `quantity` and `unit` to calculation lines.

- [ ] **Step 5: Add a v2 API method**

```ts
getPriceListV2() {
  return request<ProfessionalPriceList | PriceList>("/api/price-list?version=2");
}
```

Do not change the existing `getPriceList()` method; it remains available for explicit legacy use.

- [ ] **Step 6: Implement the unified catalog model**

`catalog.ts` should export:

```ts
export type CatalogWork = {
  id: string;
  code: string;
  group: string;
  sort_order: number;
  name_ru: string;
  name_fr: string;
  unit: WorkUnit;
  quantity_basis: QuantityBasis;
  base_unit_price: number;
  default_layers: number;
  max_layers: number;
};

export type CatalogGroup = WorkGroup & { works: CatalogWork[] };

export type Catalog = {
  version: 1 | 2;
  currency: string;
  vat_presets: number[];
  groups: CatalogGroup[];
};

export function normalizePriceList(payload: ProfessionalPriceList | PriceList): Catalog;
```

For v1, synthesize one group with `code: "legacy"`, use `quantity_basis: "area"`, preserve the API order, and use `[10, 20]` as frontend presets. For v2, ignore inactive works and sort groups/works numerically.

- [ ] **Step 7: Run tests and typecheck**

```bash
cd frontend && npm test && npm run typecheck
```

Expected: catalog tests PASS; TypeScript exits 0.

- [ ] **Step 8: Commit the catalog boundary**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/api.ts frontend/src/catalog.ts frontend/src/catalog.test.ts
git commit -m "Add Phase 1.1 frontend catalog model"
```

## Task 2: Render Grouped Works and Length Quantities

**Files:**
- Modify: `frontend/src/catalog.ts`
- Modify: `frontend/src/catalog.test.ts`
- Modify: `frontend/src/ui/RoomsPage.tsx:1-189`
- Modify: `frontend/src/i18n.tsx`
- Modify: `frontend/src/styles.css:253-270,376-403`

- [ ] **Step 1: Write failing tests for initial state and payload construction**

```ts
it("prefills acrylic with perimeter and leaves crack treatment unselected", () => {
  const state = createInitialWorkState(v2Catalog, { length: 4, width: 3 });
  expect(state.acrylic).toMatchObject({ selected: true, quantity: "14", quantityTouched: false });
  expect(state.crack_treatment).toMatchObject({ selected: false, quantity: "", quantityTouched: false });
});

it("sends quantity only for selected length works", () => {
  const payload = buildRoomWorkPayloads(v2Catalog, stateWithSixMetersOfCracks);
  expect(payload.find((work) => work.code === "crack_treatment")?.quantity).toBe(6);
  expect(payload.find((work) => work.code === "paint")).not.toHaveProperty("quantity");
});

it("keeps legacy works selected and area-based", () => {
  const state = createInitialWorkState(v1Catalog, { length: 4, width: 3 });
  expect(Object.values(state).every((work) => work.selected)).toBe(true);
  expect(buildRoomWorkPayloads(v1Catalog, state).every((work) => work.quantity === undefined)).toBe(true);
});
```

- [ ] **Step 2: Run tests and verify RED**

```bash
cd frontend && npm test
```

Expected: FAIL because state/payload helpers do not exist.

- [ ] **Step 3: Add catalog-aware form helpers**

Implement:

```ts
export type WorkFormState = Record<string, {
  selected: boolean;
  layers: number;
  unit_price: number;
  quantity: string;
  quantityTouched: boolean;
}>;

export function roomPerimeter(length: number, width: number): number;
export function createInitialWorkState(catalog: Catalog, dimensions: { length: number; width: number }): WorkFormState;
export function updateUntouchedAcrylicQuantity(state: WorkFormState, length: number, width: number): WorkFormState;
export function buildRoomWorkPayloads(catalog: Catalog, state: WorkFormState): RoomWorkPayload[];
```

Reject a selected length work with an empty/non-positive quantity in the UI before calling the API. Preserve backend error handling for `quantity_required` as a second boundary.

- [ ] **Step 4: Change RoomsPage to request and normalize v2**

Replace `api.getPriceList()` with:

```ts
api.getPriceListV2().then((payload) => {
  const catalog = normalizePriceList(payload);
  setCatalog(catalog);
  setWorks(createInitialWorkState(catalog, { length, width }));
});
```

Do not alter routes or the room/opening flow.

- [ ] **Step 5: Render work groups**

For each `catalog.groups`, render an un-nested group section with localized heading and its works. Legacy v1 uses the existing generic `t.works` heading and does not expose a new visible “legacy” label.

Each work row contains:

- checkbox and localized name;
- layers input, `min=1`, `max=work.max_layers`, integer step;
- price input with localized unit suffix (`€/m²`, `€/m.п.` / `€/ml`, `€/шт.` / `€/u`);
- quantity input only when `quantity_basis === "length"`.

Disabled/unselected rows keep their values but are omitted from payload.

- [ ] **Step 6: Keep acrylic perimeter synchronized until edited**

When room length or width changes, call `updateUntouchedAcrylicQuantity`. Once the user edits the acrylic quantity, set `quantityTouched: true` and stop automatic updates.

- [ ] **Step 7: Add RU/FR strings**

Add dictionary keys for:

```ts
quantity: "Количество" / "Quantité"
lengthQuantity: "Длина, м.п." / "Longueur, ml"
quantityRequired: "Укажите длину выбранной работы" / "Indiquez la longueur du travail sélectionné"
unitM2: "м²" / "m²"
unitMl: "м.п." / "ml"
unitU: "шт." / "u"
```

Map backend `quantity_required` to the same localized validation message.

- [ ] **Step 8: Add stable grouped layout styles**

Add `.work-group`, `.work-group-heading`, and a responsive `.professional-work-row`. Use fixed grid tracks/minmax constraints so selecting a work or showing a length input does not shift unrelated rows. At mobile width, use one column and keep labels adjacent to their controls.

- [ ] **Step 9: Run tests, typecheck, and build**

```bash
cd frontend && npm test && npm run typecheck && npm run build
```

Expected: all commands exit 0.

- [ ] **Step 10: Commit grouped work entry**

```bash
git add frontend/src/catalog.ts frontend/src/catalog.test.ts frontend/src/ui/RoomsPage.tsx frontend/src/i18n.tsx frontend/src/styles.css
git commit -m "Add grouped professional work entry"
```

## Task 3: Add TVA 10% and 20% Presets

**Files:**
- Modify: `frontend/src/ui/NewEstimatePage.tsx:1-84`
- Modify: `frontend/src/ui/EstimateView.tsx:1-110,160-190`
- Modify: `frontend/src/i18n.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add TVA state to estimate creation**

Initialize `vatPct` to `20` and replace the hardcoded create payload value:

```ts
const [vatPct, setVatPct] = useState<10 | 20>(20);

await api.createEstimate({
  title,
  address: address || null,
  locale,
  vat_pct: vatPct
});
```

- [ ] **Step 2: Render the creation presets as a segmented control**

Render two radio-backed options, `10%` and `20%`, with an accessible group label. Keep `20%` selected by default so the old MVP path produces the same result without extra interaction.

- [ ] **Step 3: Add owner estimate TVA controls**

In non-read-only `EstimateView`, render the same presets in the totals panel. On selection:

```ts
await api.updateEstimate(estimate.id, { vat_pct: nextVat });
const calculation = await api.calculateEstimate(estimate.id);
setEstimate({ ...estimate, vat_pct: nextVat, total_amount: calculation.total });
setCalculation(calculation);
```

Disable the control while saving. For an existing estimate whose TVA is neither 10 nor 20, display its saved percentage without coercing it until the user selects a preset.

- [ ] **Step 4: Keep read-only behavior unchanged**

Share view displays `estimate.vat_pct` and does not render interactive TVA controls.

- [ ] **Step 5: Add RU/FR strings and styles**

Add `vatRate`, `vatPreset10`, `vatPreset20`, and `saving` strings. Reuse the existing `.segmented` visual language and ensure the control is hidden by current print CSS only if interactive; the printed TVA percentage remains visible in totals.

- [ ] **Step 6: Verify creation and recalculation manually**

Run backend and frontend, then verify:

1. New estimate defaults to 20%.
2. Selecting 10% before creation persists `vat_pct: 10`.
3. Changing an owner estimate from 20% to 10% changes total to `subtotal × 1.10`.
4. Share view displays the saved rate without controls.

- [ ] **Step 7: Run automated checks**

```bash
cd frontend && npm test && npm run typecheck && npm run build
```

Expected: all commands exit 0.

- [ ] **Step 8: Commit TVA presets**

```bash
git add frontend/src/ui/NewEstimatePage.tsx frontend/src/ui/EstimateView.tsx frontend/src/i18n.tsx frontend/src/styles.css
git commit -m "Add TVA presets to estimate flow"
```

## Task 4: Group Estimate Lines and Preserve Legacy Editing

**Files:**
- Modify: `frontend/src/catalog.ts`
- Modify: `frontend/src/catalog.test.ts`
- Modify: `frontend/src/ui/EstimateView.tsx:35-220`
- Modify: `frontend/src/i18n.tsx`
- Modify: `frontend/src/styles.css:290-437`

- [ ] **Step 1: Write failing grouping tests for saved room works**

```ts
it("groups saved v2 room works and keeps legacy works visible", () => {
  const groups = groupRoomWorks([
    v2PaintWork,
    v2CrackWork,
    legacyPuttyWork
  ], v2Catalog);

  expect(groups.map((group) => group.code)).toEqual(["prep", "peinture", "legacy"]);
  expect(groups.at(-1)?.works[0].code).toBe("putty");
});
```

- [ ] **Step 2: Run tests and verify RED**

```bash
cd frontend && npm test
```

Expected: FAIL because `groupRoomWorks` does not exist.

- [ ] **Step 3: Implement saved-work grouping**

Export `groupRoomWorks(works, catalog?)`. Prefer `RoomWork.group`; use catalog metadata as fallback; place unknown/legacy works last without dropping them.

- [ ] **Step 4: Preserve quantity when saving edited prices**

Change the update payload mapping to include quantity only for length works:

```ts
works: room.works.map((work) => ({
  code: work.code,
  layers: work.layers,
  unit_price: prices[work.id] ?? work.unit_price,
  ...(work.quantity_basis === "length" && work.quantity != null
    ? { quantity: work.quantity }
    : {})
}))
```

This prevents `quantity_required` when editing prices on Phase 1.1 estimates and leaves old area works unchanged.

- [ ] **Step 5: Render grouped estimate sections**

Within each room, render group headings and rows in catalog order. For legacy estimates without group metadata, render the original flat table or one unlabeled legacy section.

Replace the area-only column with a localized quantity column:

- area work: calculation `quantity` or `area`, displayed as m²;
- length work: saved/calculated `quantity`, displayed as `ml`/localized m.п.;
- unit price label uses the work unit;
- consumption unit supports `l`, `kg`, `u`, and `m2`.

- [ ] **Step 6: Keep owner and share views using the same component**

Do not fork estimate rendering. `readOnly` controls only edit buttons/inputs. Group headings, quantities, units, TVA labels, and print layout are identical in owner and share views.

- [ ] **Step 7: Update print and responsive CSS**

Add non-breaking group headings, avoid page breaks immediately after a heading, and keep the totals block together. Preserve horizontal scrolling on small screens and remove it in print.

- [ ] **Step 8: Run tests and build checks**

```bash
cd frontend && npm test && npm run typecheck && npm run build
```

Expected: all commands exit 0.

- [ ] **Step 9: Commit estimate grouping**

```bash
git add frontend/src/catalog.ts frontend/src/catalog.test.ts frontend/src/ui/EstimateView.tsx frontend/src/i18n.tsx frontend/src/styles.css
git commit -m "Group Phase 1.1 estimate lines"
```

## Task 5: Browser Acceptance and Documentation

**Files:**
- Modify: `frontend/README.md`

- [ ] **Step 1: Start both applications**

Backend:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: Verify the professional catalog flow in the browser**

At desktop and mobile widths:

1. Open `/estimate/new`, choose TVA 10%, create an estimate.
2. Confirm three localized groups appear in order.
3. Confirm inactive legacy `putty` is absent from the new-room catalog.
4. Confirm `acrylic` is prefilled with `14` for a 4 × 3 room.
5. Select `crack_treatment`, enter `6`, save the room, and calculate.
6. Confirm area rows use m² and length rows use ml/m.п.
7. Confirm subtotal, TVA 10%, and total are displayed.
8. Confirm owner price edits preserve the length quantity.
9. Confirm the share route remains read-only and grouped.
10. Print preview shows group headings and totals without interactive controls.

- [ ] **Step 3: Verify legacy compatibility**

Open an estimate created before Phase 1.1 and confirm:

1. `putty`, `primer`, and `paint` all render.
2. All three use area semantics.
3. Editing prices and recalculating does not require `quantity`.
4. If the catalog response has the legacy v1 shape, the room form still renders the original three works.

- [ ] **Step 4: Update frontend documentation**

Document:

- the v2 endpoint;
- v1 response normalization/fallback;
- grouped work behavior;
- area vs length quantities;
- TVA presets;
- `npm test`, `npm run typecheck`, and `npm run build`.

- [ ] **Step 5: Run final verification**

```bash
cd frontend
npm test
npm run typecheck
npm run build
cd ..
git diff --check
git status --short
```

Expected: tests/typecheck/build exit 0; diff check has no output; only planned frontend/docs files are modified.

- [ ] **Step 6: Commit documentation and acceptance changes**

```bash
git add frontend/README.md
git commit -m "Document Phase 1.1 frontend flow"
```

## Acceptance Criteria

1. `RoomsPage` requests `/api/price-list?version=2`.
2. V2 work groups and active works render in backend sort order with RU/FR names.
3. A selected area work sends no `quantity`; calculation continues to use backend area.
4. A selected length work requires a positive quantity and sends it in the room payload.
5. Acrylic defaults to room perimeter and stops auto-updating after manual edit.
6. Crack treatment does not force a length until selected.
7. Layers respect each v2 work's `max_layers` in the UI.
8. Material units `l`, `kg`, `u`, and `m2`, plus work units `m2`, `ml`, and `u`, display correctly.
9. New estimates default to TVA 20%; presets 10% and 20% are available and persisted.
10. Changing TVA on an owner estimate recalculates the total; share view remains read-only.
11. Estimate and print views group professional lines and preserve all legacy lines.
12. Existing MVP estimates remain readable, price-editable, and recalculable without quantity errors.
13. A legacy v1 price-list response still produces the original three-work room flow.
14. No backend files or API routes are changed.
15. `npm test`, `npm run typecheck`, `npm run build`, and `git diff --check` pass.

import { describe, expect, it } from "vitest";
import type { PriceList, ProfessionalPriceList, WorkType } from "./api";
import {
  buildRoomWorkPayloads,
  createInitialWorkState,
  normalizePriceList,
  updateUntouchedAcrylicQuantity
} from "./catalog";

const v1Payload: PriceList = {
  currency: "EUR",
  work_types: [
    legacyWork("paint", "Покраска", "Peinture", 7, 2),
    legacyWork("primer", "Грунтовка", "Primaire", 2.5, 1),
    legacyWork("putty", "Шпаклёвка", "Enduit", 9.5, 2)
  ]
};

const v2Payload: ProfessionalPriceList = {
  version: 2,
  currency: "EUR",
  vat_presets: [10, 20],
  groups: [
    { code: "peinture", sort_order: 3, name_ru: "Малярные работы", name_fr: "Mise en peinture" },
    { code: "prep", sort_order: 1, name_ru: "Подготовка", name_fr: "Préparation" },
    { code: "enduits", sort_order: 2, name_ru: "Шпаклёвочные работы", name_fr: "Enduits" }
  ],
  work_types: [
    professionalWork("mesh_reinforcement", "prep", 2),
    professionalWork("putty", "enduits", 9, false),
    professionalWork("paint", "peinture", 3),
    professionalWork("putty_base", "enduits", 1),
    professionalWork("putty_finish", "enduits", 2),
    professionalWork("sanding", "enduits", 3),
    professionalWork("primer", "peinture", 1),
    professionalWork("acrylic", "peinture", 2, true, "ml", "length"),
    professionalWork("crack_treatment", "prep", 1, true, "ml", "length")
  ]
};

describe("normalizePriceList", () => {
  it("orders v2 groups and active works by sort_order", () => {
    const catalog = normalizePriceList(v2Payload);

    expect(catalog.groups.map((group) => group.code)).toEqual(["prep", "enduits", "peinture"]);
    expect(catalog.groups[0].works.map((work) => work.code)).toEqual([
      "crack_treatment",
      "mesh_reinforcement"
    ]);
    expect(catalog.groups.flatMap((group) => group.works).map((work) => work.code)).not.toContain("putty");
  });

  it("exposes eight active professional works", () => {
    const catalog = normalizePriceList(v2Payload);

    expect(catalog.groups.flatMap((group) => group.works)).toHaveLength(8);
  });

  it("normalizes the legacy response without changing its three works", () => {
    const catalog = normalizePriceList(v1Payload);

    expect(catalog.version).toBe(1);
    expect(catalog.vat_presets).toEqual([10, 20]);
    expect(catalog.groups.flatMap((group) => group.works).map((work) => work.code)).toEqual([
      "paint",
      "primer",
      "putty"
    ]);
    expect(catalog.groups[0].works.every((work) => work.quantity_basis === "area")).toBe(true);
  });
});

describe("professional work form state", () => {
  it("prefills acrylic with perimeter and leaves length works unselected", () => {
    const catalog = normalizePriceList(v2Payload);
    const state = createInitialWorkState(catalog, { length: 4, width: 3 });

    expect(state.acrylic).toMatchObject({
      selected: false,
      quantity: "14",
      quantityTouched: false
    });
    expect(state.crack_treatment).toMatchObject({
      selected: false,
      quantity: "",
      quantityTouched: false
    });
    expect(state.paint.selected).toBe(true);
  });

  it("updates untouched acrylic perimeter but preserves a manual quantity", () => {
    const catalog = normalizePriceList(v2Payload);
    const initial = createInitialWorkState(catalog, { length: 4, width: 3 });
    const resized = updateUntouchedAcrylicQuantity(initial, 5, 4);
    const edited = {
      ...resized,
      acrylic: { ...resized.acrylic, quantity: "7.5", quantityTouched: true }
    };

    expect(resized.acrylic.quantity).toBe("18");
    expect(updateUntouchedAcrylicQuantity(edited, 6, 5).acrylic.quantity).toBe("7.5");
  });

  it("sends quantity only for selected length works", () => {
    const catalog = normalizePriceList(v2Payload);
    const initial = createInitialWorkState(catalog, { length: 4, width: 3 });
    const state = {
      ...initial,
      crack_treatment: {
        ...initial.crack_treatment,
        selected: true,
        quantity: "6",
        quantityTouched: true
      }
    };

    const payload = buildRoomWorkPayloads(catalog, state);

    expect(payload.find((work) => work.code === "crack_treatment")?.quantity).toBe(6);
    expect(payload.find((work) => work.code === "paint")).not.toHaveProperty("quantity");
    expect(payload.some((work) => work.code === "acrylic")).toBe(false);
  });

  it("rejects a selected length work without a positive quantity", () => {
    const catalog = normalizePriceList(v2Payload);
    const initial = createInitialWorkState(catalog, { length: 4, width: 3 });
    const state = {
      ...initial,
      crack_treatment: { ...initial.crack_treatment, selected: true }
    };

    expect(() => buildRoomWorkPayloads(catalog, state)).toThrow("quantity_required");
  });

  it("keeps legacy works selected and area-based", () => {
    const catalog = normalizePriceList(v1Payload);
    const state = createInitialWorkState(catalog, { length: 4, width: 3 });
    const payload = buildRoomWorkPayloads(catalog, state);

    expect(Object.values(state).every((work) => work.selected)).toBe(true);
    expect(payload.every((work) => work.quantity === undefined)).toBe(true);
  });
});

function legacyWork(code: string, nameRu: string, nameFr: string, price: number, layers: number): WorkType {
  return {
    id: `${code}-id`,
    code,
    name_ru: nameRu,
    name_fr: nameFr,
    unit: "m2",
    base_unit_price: price,
    default_layers: layers,
    material: {
      name_ru: "Материал",
      name_fr: "Matériau",
      consumption_per_m2: 0.1,
      consumption_unit: "l" as const,
      package_size: 10,
      package_price: 20
    }
  };
}

function professionalWork(
  code: string,
  group: string,
  sortOrder: number,
  active = true,
  unit: "m2" | "ml" | "u" = "m2",
  quantityBasis: "area" | "length" = "area"
) {
  return {
    id: `${code}-id`,
    code,
    group,
    sort_order: sortOrder,
    name_ru: code,
    name_fr: code,
    unit,
    quantity_basis: quantityBasis,
    base_unit_price: 5,
    default_layers: 1,
    max_layers: 3,
    active,
    material: {
      name_ru: "Материал",
      name_fr: "Matériau",
      consumption_per_unit: 0.1,
      consumption_unit: "kg" as const,
      package_size: 5,
      package_price: 10
    }
  };
}

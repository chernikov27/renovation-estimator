import type {
  PriceList,
  ProfessionalPriceList,
  QuantityBasis,
  RoomWorkPayload,
  WorkGroup,
  WorkUnit
} from "./api";

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

export type CatalogGroup = WorkGroup & {
  works: CatalogWork[];
};

export type Catalog = {
  version: 1 | 2;
  currency: string;
  vat_presets: number[];
  groups: CatalogGroup[];
};

export type WorkFormState = Record<
  string,
  {
    selected: boolean;
    layers: number;
    unit_price: number;
    quantity: string;
    quantityTouched: boolean;
  }
>;

export function normalizePriceList(payload: ProfessionalPriceList | PriceList): Catalog {
  if (!isProfessionalPriceList(payload)) {
    return normalizeLegacyPriceList(payload);
  }

  const activeWorks = payload.work_types.filter((work) => work.active);
  const groups = [...payload.groups]
    .sort((left, right) => left.sort_order - right.sort_order)
    .map((group) => ({
      ...group,
      works: activeWorks
        .filter((work) => work.group === group.code)
        .sort((left, right) => left.sort_order - right.sort_order)
        .map((work) => ({
          id: work.id,
          code: work.code,
          group: work.group,
          sort_order: work.sort_order,
          name_ru: work.name_ru,
          name_fr: work.name_fr,
          unit: work.unit,
          quantity_basis: work.quantity_basis,
          base_unit_price: work.base_unit_price,
          default_layers: work.default_layers,
          max_layers: work.max_layers
        }))
    }));

  return {
    version: 2,
    currency: payload.currency,
    vat_presets: [...payload.vat_presets],
    groups
  };
}

export function roomPerimeter(length: number, width: number): number {
  return 2 * (length + width);
}

export function createInitialWorkState(
  catalog: Catalog,
  dimensions: { length: number; width: number }
): WorkFormState {
  return Object.fromEntries(
    catalog.groups.flatMap((group) =>
      group.works.map((work) => [
        work.code,
        {
          selected: work.quantity_basis === "area",
          layers: work.default_layers,
          unit_price: work.base_unit_price,
          quantity: work.code === "acrylic" ? formatQuantity(roomPerimeter(dimensions.length, dimensions.width)) : "",
          quantityTouched: false
        }
      ])
    )
  );
}

export function updateUntouchedAcrylicQuantity(
  state: WorkFormState,
  length: number,
  width: number
): WorkFormState {
  const acrylic = state.acrylic;
  if (!acrylic || acrylic.quantityTouched) {
    return state;
  }
  return {
    ...state,
    acrylic: {
      ...acrylic,
      quantity: formatQuantity(roomPerimeter(length, width))
    }
  };
}

export function buildRoomWorkPayloads(catalog: Catalog, state: WorkFormState): RoomWorkPayload[] {
  return catalog.groups.flatMap((group) =>
    group.works.flatMap((work) => {
      const value = state[work.code];
      if (!value?.selected) {
        return [];
      }

      const payload: RoomWorkPayload = {
        code: work.code,
        layers: value.layers,
        unit_price: value.unit_price
      };
      if (work.quantity_basis === "length") {
        const quantity = Number(value.quantity);
        if (!Number.isFinite(quantity) || quantity <= 0) {
          throw new Error("quantity_required");
        }
        payload.quantity = quantity;
      }
      return [payload];
    })
  );
}

function normalizeLegacyPriceList(payload: PriceList): Catalog {
  return {
    version: 1,
    currency: payload.currency,
    vat_presets: [10, 20],
    groups: [
      {
        code: "legacy",
        sort_order: 0,
        name_ru: "Работы",
        name_fr: "Travaux",
        works: payload.work_types.map((work, index) => ({
          id: work.id,
          code: work.code,
          group: "legacy",
          sort_order: index,
          name_ru: work.name_ru,
          name_fr: work.name_fr,
          unit: work.unit,
          quantity_basis: "area",
          base_unit_price: work.base_unit_price,
          default_layers: work.default_layers,
          max_layers: 5
        }))
      }
    ]
  };
}

function isProfessionalPriceList(
  payload: ProfessionalPriceList | PriceList
): payload is ProfessionalPriceList {
  return "version" in payload && payload.version === 2;
}

function formatQuantity(value: number): string {
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(2)));
}

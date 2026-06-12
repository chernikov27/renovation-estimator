export type Locale = "ru" | "fr";
export type WorkUnit = "m2" | "ml" | "u";
export type QuantityBasis = "area" | "length";
export type MaterialUnit = "l" | "kg" | "u" | "m2";

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type WorkType = {
  id: string;
  code: string;
  name_ru: string;
  name_fr: string;
  unit: WorkUnit;
  base_unit_price: number;
  default_layers: number;
  material: {
    name_ru: string;
    name_fr: string;
    consumption_per_m2: number;
    consumption_unit: "l" | "kg";
    package_size: number;
    package_price: number;
  };
};

export type PriceList = {
  currency: string;
  work_types: WorkType[];
};

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

export type OpeningPayload = {
  kind: "window" | "door";
  width_m: number;
  height_m: number;
  count: number;
};

export type RoomWorkPayload = {
  code: string;
  layers: number;
  unit_price?: number;
  quantity?: number;
};

export type RoomPayload = {
  name: string;
  length_m: number;
  width_m: number;
  height_m: number;
  include_ceiling: boolean;
  openings: OpeningPayload[];
  works: RoomWorkPayload[];
};

export type Estimate = {
  id: string;
  title: string;
  address: string | null;
  locale: Locale;
  currency: string;
  vat_pct: number;
  share_token: string;
  total_amount: number | null;
  rooms: Room[];
  photos: unknown[];
};

export type Room = {
  id: string;
  estimate_id: string;
  name: string;
  length_m: number;
  width_m: number;
  height_m: number;
  include_ceiling: boolean;
  openings: Array<OpeningPayload & { id: string }>;
  works: RoomWork[];
};

export type RoomWork = {
  id: string;
  code: string;
  name_ru: string;
  name_fr: string;
  group: string | null;
  unit: WorkUnit;
  quantity_basis: QuantityBasis;
  quantity: number | null;
  layers: number;
  unit_price: number;
  material_consumption_per_m2: number;
  material_consumption_unit: MaterialUnit;
  material_package_size: number;
  material_package_price: number;
  computed_area: number | null;
  labor_cost: number | null;
  material_cost: number | null;
};

export type CalculationResult = {
  subtotal: number;
  vat_pct: number;
  total: number;
  warnings: Array<{ code: string; message: string; room_id: string | null }>;
  rooms: Array<{
    id: string;
    name: string;
    walls_area: number;
    ceiling_area: number;
    base_area: number;
    lines: Array<{
      code: string;
      layers: number;
      area: number;
      quantity: number;
      unit: WorkUnit;
      labor_cost: number;
      consumption: number;
      packages: number;
      material_cost: number;
      total_cost: number;
    }>;
  }>;
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    }
  });
  if (!response.ok) {
    const payload: ErrorEnvelope | null = await response.json().catch(() => null);
    const code = payload?.error?.code ?? "http_error";
    const message = payload?.error?.message ?? `HTTP ${response.status}`;
    throw new ApiError(code, message, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  createEstimate(payload: { title: string; address?: string | null; locale: Locale; vat_pct?: number }) {
    return request<Estimate>("/api/estimates", { method: "POST", body: JSON.stringify(payload) });
  },
  getEstimate(id: string) {
    return request<Estimate>(`/api/estimates/${id}`);
  },
  updateEstimate(id: string, payload: Partial<Pick<Estimate, "title" | "address" | "locale" | "vat_pct">>) {
    return request<Estimate>(`/api/estimates/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  createRoom(estimateId: string, payload: RoomPayload) {
    return request<Room>(`/api/estimates/${estimateId}/rooms`, { method: "POST", body: JSON.stringify(payload) });
  },
  updateRoom(roomId: string, payload: RoomPayload) {
    return request<Room>(`/api/rooms/${roomId}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  calculateEstimate(id: string) {
    return request<CalculationResult>(`/api/estimates/${id}/calculate`, { method: "POST" });
  },
  getShared(token: string) {
    return request<Estimate>(`/api/shared/${token}`);
  },
  getPriceList() {
    return request<PriceList>("/api/price-list");
  },
  getPriceListV2() {
    return request<ProfessionalPriceList | PriceList>("/api/price-list?version=2");
  }
};

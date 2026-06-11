export type StoredEstimate = {
  id: string;
  title: string;
};

const key = "renovation_estimate_ids";

export function getStoredEstimates(): StoredEstimate[] {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]") as StoredEstimate[];
  } catch {
    return [];
  }
}

export function saveStoredEstimate(estimate: StoredEstimate): void {
  const current = getStoredEstimates().filter((item) => item.id !== estimate.id);
  localStorage.setItem(key, JSON.stringify([estimate, ...current].slice(0, 20)));
}

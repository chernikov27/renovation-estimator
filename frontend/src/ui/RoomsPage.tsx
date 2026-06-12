import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { OpeningPayload, RoomPayload, WorkUnit } from "../api";
import { api } from "../api";
import {
  buildRoomWorkPayloads,
  createInitialWorkState,
  normalizePriceList,
  updateUntouchedAcrylicQuantity,
  type Catalog,
  type WorkFormState
} from "../catalog";
import { translateError, useI18n } from "../i18n";

export function RoomsPage() {
  const { estimateId } = useParams();
  const navigate = useNavigate();
  const { locale, t } = useI18n();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [name, setName] = useState("Комната 1");
  const [length, setLength] = useState(4);
  const [width, setWidth] = useState(3);
  const [height, setHeight] = useState(2.7);
  const [includeCeiling, setIncludeCeiling] = useState(true);
  const [openings, setOpenings] = useState<OpeningPayload[]>([
    { kind: "window", width_m: 1.5, height_m: 1.4, count: 1 },
    { kind: "door", width_m: 0.9, height_m: 2.05, count: 1 }
  ]);
  const [works, setWorks] = useState<WorkFormState>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getPriceListV2()
      .then((payload) => {
        const nextCatalog = normalizePriceList(payload);
        setCatalog(nextCatalog);
        setWorks(createInitialWorkState(nextCatalog, { length, width }));
      })
      .catch((err) => setError(translateError(err, t)));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!estimateId || !catalog) {
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const payload: RoomPayload = {
        name,
        length_m: length,
        width_m: width,
        height_m: height,
        include_ceiling: includeCeiling,
        openings,
        works: buildRoomWorkPayloads(catalog, works)
      };
      await api.createRoom(estimateId, payload);
      await api.calculateEstimate(estimateId);
      navigate(`/estimate/${estimateId}`);
    } catch (err) {
      setError(err instanceof Error && err.message === "quantity_required" ? t.quantityRequired : translateError(err, t));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="screen">
      <div className="stepper">
        <span>1</span>
        <span className="active">2</span>
      </div>
      <div className="screen-heading">
        <h1>{t.roomsStep}</h1>
        {estimateId && (
          <Link className="button secondary" to={`/estimate/${estimateId}`}>
            {t.backToEstimate}
          </Link>
        )}
      </div>
      <form className="workspace" onSubmit={submit}>
        <section className="panel form-grid">
          <h2>{t.dimensions}</h2>
          <label>
            {t.title}
            <input value={name} maxLength={80} onChange={(event) => setName(event.target.value)} />
          </label>
          <div className="three-grid">
            <NumberField label={t.length} value={length} setValue={(value) => updateDimensions(value, width)} />
            <NumberField label={t.width} value={width} setValue={(value) => updateDimensions(length, value)} />
            <NumberField label={t.height} value={height} setValue={setHeight} />
          </div>
          <label className="check-row">
            <input type="checkbox" checked={includeCeiling} onChange={(event) => setIncludeCeiling(event.target.checked)} />
            {t.includeCeiling}
          </label>
        </section>

        <section className="panel form-grid">
          <h2>{t.openings}</h2>
          {openings.map((opening, index) => (
            <div className="opening-row" key={index}>
              <select
                value={opening.kind}
                onChange={(event) => updateOpening(index, { kind: event.target.value as OpeningPayload["kind"] })}
              >
                <option value="window">{t.addWindow}</option>
                <option value="door">{t.addDoor}</option>
              </select>
              <NumberField label={t.width} value={opening.width_m} setValue={(value) => updateOpening(index, { width_m: value })} />
              <NumberField label={t.height} value={opening.height_m} setValue={(value) => updateOpening(index, { height_m: value })} />
              <NumberField label={t.count} value={opening.count} setValue={(value) => updateOpening(index, { count: value })} step={1} />
            </div>
          ))}
          <div className="button-row">
            <button className="button secondary" type="button" onClick={() => setOpenings([...openings, { kind: "window", width_m: 1.5, height_m: 1.4, count: 1 }])}>
              {t.addWindow}
            </button>
            <button className="button secondary" type="button" onClick={() => setOpenings([...openings, { kind: "door", width_m: 0.9, height_m: 2.05, count: 1 }])}>
              {t.addDoor}
            </button>
          </div>
        </section>

        <section className="panel form-grid">
          <h2>{t.works}</h2>
          {!catalog ? (
            <p>{t.loading}</p>
          ) : (
            catalog.groups.map((group) => (
              <section className="work-group" key={group.code}>
                {catalog.version === 2 && (
                  <h3 className="work-group-heading">{locale === "fr" ? group.name_fr : group.name_ru}</h3>
                )}
                {group.works.map((workType) => {
                  const state = works[workType.code];
                  return (
                    <div className="professional-work-row" key={workType.code}>
                      <label className="check-row work-name">
                        <input
                          type="checkbox"
                          checked={state?.selected ?? false}
                          onChange={(event) => updateWork(workType.code, { selected: event.target.checked })}
                        />
                        {locale === "fr" ? workType.name_fr : workType.name_ru}
                      </label>
                      <NumberField
                        label={t.layers}
                        value={state?.layers ?? workType.default_layers}
                        setValue={(value) => updateWork(workType.code, { layers: value })}
                        min={1}
                        max={workType.max_layers}
                        step={1}
                      />
                      <NumberField
                        label={`${t.unitPrice.replace("m²", unitLabel(workType.unit, t))}`}
                        value={state?.unit_price ?? workType.base_unit_price}
                        setValue={(value) => updateWork(workType.code, { unit_price: value })}
                        min={0}
                      />
                      {workType.quantity_basis === "length" ? (
                        <label>
                          {t.lengthQuantity}
                          <input
                            min="0.01"
                            step="0.01"
                            type="number"
                            value={state?.quantity ?? ""}
                            onChange={(event) => updateWork(workType.code, {
                              quantity: event.target.value,
                              quantityTouched: true
                            })}
                          />
                        </label>
                      ) : (
                        <span className="work-unit-note">{unitLabel(workType.unit, t)}</span>
                      )}
                    </div>
                  );
                })}
              </section>
            ))
          )}
          {error && <p className="error-text">{error}</p>}
          <button className="button primary wide" disabled={saving || !catalog} type="submit">
            {saving ? t.loading : t.saveRoom}
          </button>
        </section>
      </form>
    </section>
  );

  function updateOpening(index: number, patch: Partial<OpeningPayload>) {
    setOpenings(openings.map((opening, current) => (current === index ? { ...opening, ...patch } : opening)));
  }

  function updateDimensions(nextLength: number, nextWidth: number) {
    setLength(nextLength);
    setWidth(nextWidth);
    setWorks((current) => updateUntouchedAcrylicQuantity(current, nextLength, nextWidth));
  }

  function updateWork(code: string, patch: Partial<WorkFormState[string]>) {
    setWorks((current) => ({
      ...current,
      [code]: { ...current[code], ...patch }
    }));
  }
}

function NumberField({
  label,
  value,
  setValue,
  step = 0.01,
  min,
  max
}: {
  label: string;
  value: number;
  setValue: (value: number) => void;
  step?: number;
  min?: number;
  max?: number;
}) {
  return (
    <label>
      {label}
      <input min={min} max={max} type="number" step={step} value={value} onChange={(event) => setValue(Number(event.target.value))} />
    </label>
  );
}

function unitLabel(unit: WorkUnit, t: { unitM2: string; unitMl: string; unitU: string }) {
  return unit === "ml" ? t.unitMl : unit === "u" ? t.unitU : t.unitM2;
}

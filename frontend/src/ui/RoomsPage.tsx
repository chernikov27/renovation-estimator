import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { OpeningPayload, PriceList, RoomPayload, RoomWorkPayload } from "../api";
import { api } from "../api";
import { translateError, useI18n } from "../i18n";

export function RoomsPage() {
  const { estimateId } = useParams();
  const navigate = useNavigate();
  const { locale, t } = useI18n();
  const [priceList, setPriceList] = useState<PriceList | null>(null);
  const [name, setName] = useState("Комната 1");
  const [length, setLength] = useState(4);
  const [width, setWidth] = useState(3);
  const [height, setHeight] = useState(2.7);
  const [includeCeiling, setIncludeCeiling] = useState(true);
  const [openings, setOpenings] = useState<OpeningPayload[]>([
    { kind: "window", width_m: 1.5, height_m: 1.4, count: 1 },
    { kind: "door", width_m: 0.9, height_m: 2.05, count: 1 }
  ]);
  const [works, setWorks] = useState<Record<string, { selected: boolean; layers: number; unit_price: number }>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getPriceList()
      .then((list) => {
        setPriceList(list);
        setWorks(
          Object.fromEntries(
            list.work_types.map((work) => [
              work.code,
              {
                selected: true,
                layers: work.default_layers,
                unit_price: work.base_unit_price
              }
            ])
          )
        );
      })
      .catch((err) => setError(translateError(err, t)));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!estimateId || !priceList) {
      return;
    }
    const selectedWorks: RoomWorkPayload[] = Object.entries(works)
      .filter(([, value]) => value.selected)
      .map(([code, value]) => ({ code, layers: value.layers, unit_price: value.unit_price }));
    const payload: RoomPayload = {
      name,
      length_m: length,
      width_m: width,
      height_m: height,
      include_ceiling: includeCeiling,
      openings,
      works: selectedWorks
    };

    setSaving(true);
    setError(null);
    try {
      await api.createRoom(estimateId, payload);
      await api.calculateEstimate(estimateId);
      navigate(`/estimate/${estimateId}`);
    } catch (err) {
      setError(translateError(err, t));
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
            <NumberField label={t.length} value={length} setValue={setLength} />
            <NumberField label={t.width} value={width} setValue={setWidth} />
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
          {!priceList ? (
            <p>{t.loading}</p>
          ) : (
            priceList.work_types.map((workType) => {
              const state = works[workType.code];
              return (
                <div className="work-row" key={workType.code}>
                  <label className="check-row">
                    <input
                      type="checkbox"
                      checked={state?.selected ?? false}
                      onChange={(event) => setWorks({ ...works, [workType.code]: { ...state, selected: event.target.checked } })}
                    />
                    {locale === "fr" ? workType.name_fr : workType.name_ru}
                  </label>
                  <NumberField label={t.layers} value={state?.layers ?? workType.default_layers} setValue={(value) => setWorks({ ...works, [workType.code]: { ...state, layers: value } })} step={1} />
                  <NumberField label={t.unitPrice} value={state?.unit_price ?? workType.base_unit_price} setValue={(value) => setWorks({ ...works, [workType.code]: { ...state, unit_price: value } })} />
                </div>
              );
            })
          )}
          {error && <p className="error-text">{error}</p>}
          <button className="button primary wide" disabled={saving || !priceList} type="submit">
            {saving ? t.loading : t.saveRoom}
          </button>
        </section>
      </form>
    </section>
  );

  function updateOpening(index: number, patch: Partial<OpeningPayload>) {
    setOpenings(openings.map((opening, current) => (current === index ? { ...opening, ...patch } : opening)));
  }
}

function NumberField({
  label,
  value,
  setValue,
  step = 0.01
}: {
  label: string;
  value: number;
  setValue: (value: number) => void;
  step?: number;
}) {
  return (
    <label>
      {label}
      <input type="number" step={step} value={value} onChange={(event) => setValue(Number(event.target.value))} />
    </label>
  );
}

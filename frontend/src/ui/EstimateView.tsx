import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { CalculationResult, Estimate, MaterialUnit, RoomPayload } from "../api";
import { api } from "../api";
import { translateError, useI18n } from "../i18n";

export function EstimateView({
  estimateId,
  shareToken,
  readOnly
}: {
  estimateId?: string;
  shareToken?: string;
  readOnly: boolean;
}) {
  const { locale, t } = useI18n();
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [calculation, setCalculation] = useState<CalculationResult | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadEstimate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estimateId, shareToken]);

  const shareUrl = useMemo(() => {
    if (!estimate) {
      return "";
    }
    return `${window.location.origin}/s/${estimate.share_token}`;
  }, [estimate]);

  async function loadEstimate() {
    setError(null);
    try {
      const payload = shareToken ? await api.getShared(shareToken) : await api.getEstimate(estimateId ?? "");
      setEstimate(payload);
      setPrices(Object.fromEntries(payload.rooms.flatMap((room) => room.works.map((work) => [work.id, work.unit_price]))));
      if (!shareToken && payload.rooms.length > 0) {
        const calc = await api.calculateEstimate(payload.id);
        setCalculation(calc);
      }
    } catch (err) {
      setError(translateError(err, t));
    }
  }

  async function savePrices() {
    if (!estimate) {
      return;
    }
    setError(null);
    try {
      for (const room of estimate.rooms) {
        const payload: RoomPayload = {
          name: room.name,
          length_m: room.length_m,
          width_m: room.width_m,
          height_m: room.height_m,
          include_ceiling: room.include_ceiling,
          openings: room.openings.map(({ kind, width_m, height_m, count }) => ({ kind, width_m, height_m, count })),
          works: room.works.map((work) => ({ code: work.code, layers: work.layers, unit_price: prices[work.id] ?? work.unit_price }))
        };
        await api.updateRoom(room.id, payload);
      }
      const calc = await api.calculateEstimate(estimate.id);
      setCalculation(calc);
      await loadEstimate();
    } catch (err) {
      setError(translateError(err, t));
    }
  }

  if (error) {
    return <p className="error-text">{t.error}: {error}</p>;
  }
  if (!estimate) {
    return <p>{t.loading}</p>;
  }

  return (
    <section className="screen estimate-screen">
      <div className="screen-heading print-heading">
        <div>
          <h1>{estimate.title}</h1>
          <p className="muted">{estimate.address}</p>
          {readOnly && <p className="readonly-label">{t.readOnly}</p>}
        </div>
        <div className="button-row no-print">
          {!readOnly && <Link className="button secondary" to={`/estimate/${estimate.id}/rooms`}>{t.roomsStep}</Link>}
          {!readOnly && <button className="button secondary" type="button" onClick={savePrices}>{t.editPrices}</button>}
          <button className="button secondary" type="button" onClick={() => window.print()}>{t.print}</button>
          {!readOnly && (
            <button
              className="button primary"
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(shareUrl);
                setCopied(true);
              }}
            >
              {copied ? t.shareCopied : t.share}
            </button>
          )}
        </div>
      </div>

      {estimate.rooms.length === 0 ? (
        <div className="empty-state">
          <p>{t.noRooms}</p>
          {!readOnly && <Link className="button primary" to={`/estimate/${estimate.id}/rooms`}>{t.roomsStep}</Link>}
        </div>
      ) : (
        <div className="estimate-layout">
          <div className="panel table-panel">
            {estimate.rooms.map((room) => (
              <section className="room-section" key={room.id}>
                <h2>{room.name || t.roomsStep}</h2>
                <p className="muted">
                  {room.length_m} × {room.width_m} × {room.height_m} m
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>{t.works}</th>
                      <th>{t.layers}</th>
	                      <th>{t.area}</th>
	                      <th>{t.unitPrice}</th>
	                      <th>{t.labor}</th>
	                      <th>{t.consumption}</th>
	                      <th>{t.packages}</th>
	                      <th>{t.material}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {room.works.map((work) => {
                      const line = calculation?.rooms
                        .find((calcRoom) => calcRoom.id === room.id)
                        ?.lines.find((item) => item.code === work.code);
                      return (
                        <tr key={work.id}>
                          <td>{locale === "fr" ? work.name_fr : work.name_ru}</td>
                          <td>{work.layers}</td>
	                          <td>{formatNumber(line?.area ?? work.computed_area, locale)}</td>
	                          <td>
	                            {readOnly ? (
	                              money(work.unit_price, locale)
	                            ) : (
	                              <input
                                className="price-input"
                                type="number"
                                step="0.01"
                                value={prices[work.id] ?? work.unit_price}
                                onChange={(event) => setPrices({ ...prices, [work.id]: Number(event.target.value) })}
                              />
	                            )}
	                          </td>
	                          <td>{money(line?.labor_cost ?? work.labor_cost, locale)}</td>
	                          <td>{formatConsumption(line?.consumption, work.material_consumption_unit, locale)}</td>
	                          <td>{formatPackages(line?.packages, locale)}</td>
	                          <td>{money(line?.material_cost ?? work.material_cost, locale)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </section>
            ))}
          </div>
          <aside className="panel totals-panel">
            <h2>{t.totals}</h2>
            <dl>
              <div>
                <dt>{t.subtotal}</dt>
                <dd>{money(calculation?.subtotal, locale)}</dd>
              </div>
              <div>
                <dt>{t.vat}</dt>
                <dd>{calculation?.vat_pct ?? estimate.vat_pct}%</dd>
              </div>
              <div className="grand-total">
                <dt>{t.total}</dt>
                <dd>{money(calculation?.total ?? estimate.total_amount, locale)}</dd>
              </div>
            </dl>
            {!readOnly && <p className="share-url">{shareUrl}</p>}
          </aside>
        </div>
      )}
    </section>
  );
}

function money(value: number | null | undefined, locale: "ru" | "fr") {
  if (value === null || value === undefined) {
    return "–";
  }
  return new Intl.NumberFormat(numberLocale(locale), { style: "currency", currency: "EUR" }).format(value);
}

function formatNumber(value: number | null | undefined, locale: "ru" | "fr") {
  if (value === null || value === undefined) {
    return "–";
  }
  return new Intl.NumberFormat(numberLocale(locale), { maximumFractionDigits: 2 }).format(value);
}

function formatConsumption(value: number | null | undefined, unit: MaterialUnit, locale: "ru" | "fr") {
  if (value === null || value === undefined) {
    return "–";
  }
  return `${formatNumber(value, locale)} ${unit}`;
}

function formatPackages(value: number | null | undefined, locale: "ru" | "fr") {
  if (value === null || value === undefined) {
    return "–";
  }
  return new Intl.NumberFormat(numberLocale(locale), { maximumFractionDigits: 0 }).format(value);
}

function numberLocale(locale: "ru" | "fr") {
  return locale === "fr" ? "fr-FR" : "ru-RU";
}

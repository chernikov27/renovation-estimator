import { Link } from "react-router-dom";
import { getStoredEstimates } from "../storage";
import { useI18n } from "../i18n";

export function HomePage() {
  const { t } = useI18n();
  const estimates = getStoredEstimates();

  return (
    <section className="screen">
      <div className="screen-heading">
        <h1>{t.recentEstimates}</h1>
        <Link className="button primary" to="/estimate/new">
          {t.newEstimate}
        </Link>
      </div>
      {estimates.length === 0 ? (
        <div className="empty-state">
          <p>{t.emptyHome}</p>
        </div>
      ) : (
        <div className="estimate-list">
          {estimates.map((estimate) => (
            <Link className="estimate-row" key={estimate.id} to={`/estimate/${estimate.id}`}>
              <span>{estimate.title}</span>
              <span className="muted">{estimate.id.slice(0, 8)}</span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

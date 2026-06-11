import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { I18nProvider, useI18n } from "../i18n";

function Header() {
  const { locale, setLocale, t } = useI18n();
  return (
    <header className="app-header">
      <Link to="/" className="brand" aria-label={t.home}>
        <span className="brand-mark">RE</span>
        <span>{t.appName}</span>
      </Link>
      <nav className="header-actions">
        <Link to="/estimate/new" className="button primary">
          {t.newEstimate}
        </Link>
        <div className="segmented" aria-label={t.languageLabel}>
          <button className={locale === "ru" ? "active" : ""} onClick={() => setLocale("ru")} type="button">
            RU
          </button>
          <button className={locale === "fr" ? "active" : ""} onClick={() => setLocale("fr")} type="button">
            FR
          </button>
        </div>
      </nav>
    </header>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <I18nProvider>
      <Header />
      <main className="page">{children}</main>
    </I18nProvider>
  );
}

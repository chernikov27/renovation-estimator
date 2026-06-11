import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { translateError, useI18n, type Dictionary } from "../i18n";
import { saveStoredEstimate } from "../storage";

const allowedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);

export function NewEstimatePage() {
  const { locale, t } = useI18n();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [address, setAddress] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const photoError = useMemo(() => validatePhotos(files, t), [files, t]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (photoError) {
      setError(photoError);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const estimate = await api.createEstimate({ title, address: address || null, locale, vat_pct: 20 });
      saveStoredEstimate({ id: estimate.id, title: estimate.title });
      navigate(`/estimate/${estimate.id}/rooms`);
    } catch (err) {
      setError(translateError(err, t));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="screen narrow">
      <div className="stepper">
        <span className="active">1</span>
        <span>2</span>
      </div>
      <h1>{t.objectStep}</h1>
      <form className="panel form-grid" onSubmit={submit}>
        <label>
          {t.title}
          <input required maxLength={120} value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        <label>
          {t.address}
          <input maxLength={250} value={address} onChange={(event) => setAddress(event.target.value)} />
        </label>
        <label>
          {t.photos}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <p className="hint">{t.photosHint}</p>
        <p className="hint">{t.photoUploadUnavailable}</p>
        {files.length > 0 && (
          <div className="file-list">
            {files.map((file) => (
              <span key={`${file.name}-${file.size}`}>{file.name}</span>
            ))}
          </div>
        )}
        {(error || photoError) && <p className="error-text">{error || photoError}</p>}
        <button className="button primary wide" disabled={saving || !title} type="submit">
          {saving ? t.loading : t.next}
        </button>
      </form>
    </section>
  );
}

function validatePhotos(files: File[], t: Dictionary): string | null {
  if (files.length > 10) {
    return t.photoValidationMaxCount;
  }
  for (const file of files) {
    if (!allowedTypes.has(file.type)) {
      return `${file.name}: ${t.photoValidationUnsupportedType}`;
    }
    if (file.size > 10 * 1024 * 1024) {
      return `${file.name}: ${t.photoValidationMaxSize}`;
    }
  }
  return null;
}

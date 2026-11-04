import { useState, type FormEvent } from "react";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import { CheckIcon } from "../../components/Icons";
import { ErrorMessage, Spinner } from "../../components/ui";
import { usePageTitle, useSiteSettings } from "../../site/SiteContext";

const DEFAULT_ACCENT = "#2f5d4e";
const PRESETS = ["#2f5d4e", "#a8432a", "#2b4c7e", "#8a6420", "#5b4a7a", "#1f1f1f"];

export function BrandingPage() {
  usePageTitle("Оформление");
  const { loaded } = useSiteSettings();
  return loaded ? <BrandingForm /> : <Spinner />;
}

function BrandingForm() {
  const { site, setSite } = useSiteSettings();
  const [siteName, setSiteName] = useState(site.site_name);
  const [logoUrl, setLogoUrl] = useState(site.logo_url ?? "");
  const [accent, setAccent] = useState(site.accent_color ?? DEFAULT_ACCENT);
  const [showBadge, setShowBadge] = useState(site.hero_badge !== null);
  const [badge, setBadge] = useState(site.hero_badge ?? "Первые уроки — бесплатно");
  const [heroTitle, setHeroTitle] = useState(site.hero_title);
  const [heroText, setHeroText] = useState(site.hero_text ?? "");
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.updateSite({
        site_name: siteName,
        logo_url: logoUrl.trim() || null,
        accent_color: accent === DEFAULT_ACCENT ? null : accent,
        hero_badge: showBadge ? badge : null,
        hero_title: heroTitle,
        hero_text: heroText.trim() || null,
      });
      setSite(updated);
      setSaved(true);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <div>
        <h2 className="form-title">Оформление сайта</h2>
        <p className="muted">Название, логотип, цвет и текст на главной. Изменения видны всем сразу после сохранения.</p>
      </div>

      <div className="form-row">
        <label className="field">
          <span>Название сайта</span>
          <input required maxLength={100} value={siteName} onChange={(event) => setSiteName(event.target.value)} />
        </label>
        <div className="cover-field">
          <label className="field">
            <span>Логотип (ссылка на картинку)</span>
            <input
              type="url"
              placeholder="https://… .png или .svg — пусто: без логотипа"
              value={logoUrl}
              onChange={(event) => setLogoUrl(event.target.value)}
            />
            <small className="muted">Квадратный, от 64×64. Он же станет иконкой вкладки.</small>
          </label>
          {logoUrl.trim() && <img className="logo-preview" src={logoUrl.trim()} alt="Предпросмотр логотипа" />}
        </div>
      </div>

      <fieldset className="field">
        <legend>Акцентный цвет</legend>
        <div className="color-picker">
          <input
            type="color"
            aria-label="Выбрать цвет"
            value={accent}
            onChange={(event) => setAccent(event.target.value)}
          />
          <div className="swatches">
            {PRESETS.map((color) => (
              <button
                key={color}
                type="button"
                className={color === accent ? "swatch is-active" : "swatch"}
                style={{ background: color }}
                aria-label={`Цвет ${color}`}
                onClick={() => setAccent(color)}
              />
            ))}
          </div>
          <code>{accent}</code>
        </div>
        <small className="muted">
          Кнопки, ссылки и баннер на главной. Для тёмной темы оттенок подбирается автоматически.
        </small>
      </fieldset>

      <fieldset className="field">
        <legend>Баннер на главной</legend>
        <label className="checkbox">
          <input type="checkbox" checked={showBadge} onChange={(event) => setShowBadge(event.target.checked)} />
          <span>Показывать метку над заголовком</span>
        </label>
        {showBadge && (
          <input aria-label="Текст метки" required maxLength={100} value={badge} onChange={(event) => setBadge(event.target.value)} />
        )}
      </fieldset>

      <label className="field">
        <span>Заголовок</span>
        <textarea rows={2} required maxLength={200} value={heroTitle} onChange={(event) => setHeroTitle(event.target.value)} />
        <small className="muted">Перенос строки — Enter.</small>
      </label>
      <label className="field">
        <span>Текст под заголовком</span>
        <textarea
          rows={2}
          maxLength={500}
          placeholder="Пусто — текст подставится сам (с упоминанием вопросов, если они есть в курсах)"
          value={heroText}
          onChange={(event) => setHeroText(event.target.value)}
        />
      </label>

      {error && <ErrorMessage error={error} />}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Сохраняем…" : "Сохранить"}
        </button>
        {saved && (
          <span className="saved">
            <CheckIcon /> Сохранено
          </span>
        )}
      </div>
    </form>
  );
}

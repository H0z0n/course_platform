import { useState, type FormEvent } from "react";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { Course } from "../../api/types";
import { CheckIcon } from "../../components/Icons";
import { ErrorMessage } from "../../components/ui";
import { normalizePrice } from "../../lib/format";
import { slugify } from "../../lib/slugify";
import { useSite } from "../../site/SiteContext";

export function CourseForm({
  initial,
  onSaved,
}: {
  initial?: Course;
  onSaved: (course: Course) => void;
}) {
  const { currency } = useSite();
  const [title, setTitle] = useState(initial?.title ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [slugEdited, setSlugEdited] = useState(initial !== undefined);
  const [price, setPrice] = useState(initial?.price ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [coverUrl, setCoverUrl] = useState(initial?.cover_image_url ?? "");
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    setError(null);
    const data = {
      title,
      slug,
      price: normalizePrice(price),
      description,
      cover_image_url: coverUrl.trim() || null,
    };
    try {
      const course = initial
        ? await api.courses.update(initial.id, data)
        : await api.courses.create(data);
      setSaved(true);
      onSaved(course);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <label className="field">
        <span>Название курса</span>
        <input
          required
          maxLength={200}
          value={title}
          onChange={(event) => {
            setTitle(event.target.value);
            if (!slugEdited) setSlug(slugify(event.target.value));
          }}
        />
      </label>
      <div className="form-row">
        <label className="field">
          <span>Адрес страницы</span>
          <div className="input-prefix">
            <span>/courses/</span>
            <input
              required
              maxLength={100}
              pattern="[a-z0-9]+(-[a-z0-9]+)*"
              title="Строчные латинские буквы, цифры и дефисы"
              value={slug}
              onChange={(event) => {
                setSlug(event.target.value);
                setSlugEdited(true);
              }}
            />
          </div>
        </label>
        <label className="field">
          <span>Цена всего курса, {currency}</span>
          <input
            inputMode="decimal"
            placeholder="Пусто — целиком не продаётся"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
          />
        </label>
      </div>
      <div className="cover-field">
        <label className="field">
          <span>Картинка курса (ссылка)</span>
          <input
            type="url"
            placeholder="https://… .jpg или .png — пусто: цветная плашка"
            value={coverUrl}
            onChange={(event) => setCoverUrl(event.target.value)}
          />
          <small className="muted">Лучше горизонтальная, примерно 16:9.</small>
        </label>
        {coverUrl.trim() && <img className="cover-preview" src={coverUrl.trim()} alt="Предпросмотр картинки" />}
      </div>
      <label className="field">
        <span>Описание (Markdown)</span>
        <textarea
          rows={6}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>
      {error && <ErrorMessage error={error} />}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Сохраняем…" : initial ? "Сохранить" : "Создать курс"}
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

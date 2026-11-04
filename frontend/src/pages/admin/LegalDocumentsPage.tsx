import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { LegalPage } from "../../api/types";
import { CheckIcon } from "../../components/Icons";
import { MarkdownView } from "../../components/LessonContent";
import { ErrorMessage, Spinner } from "../../components/ui";
import { useApi } from "../../lib/useApi";
import { usePageTitle } from "../../site/SiteContext";

function DocumentForm({ page, onSaved }: { page: LegalPage; onSaved: (page: LegalPage) => void }) {
  const [title, setTitle] = useState(page.title);
  const [content, setContent] = useState(page.content);
  const [tab, setTab] = useState<"edit" | "preview">("edit");
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const placeholders = content.match(/\[[А-ЯЁA-Z][^\]]*\]/g) ?? [];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    setError(null);
    try {
      onSaved(await api.legal.update(page.slug, { title, content }));
      setSaved(true);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <div className="field-head">
        <h2 className="form-title">{page.title}</h2>
        <Link to={`/legal/${page.slug}`} target="_blank" className="btn btn-ghost btn-sm">
          Открыть на сайте
        </Link>
      </div>
      {page.is_template && (
        <div className="alert alert-info">
          Это шаблон. Заполните поля в квадратных скобках и покажите текст юристу — шаблон не заменяет
          юридическую консультацию.
        </div>
      )}
      {placeholders.length > 0 && (
        <p className="small muted">
          Не заполнено: {Array.from(new Set(placeholders)).join(", ")}
        </p>
      )}
      <label className="field">
        <span>Заголовок</span>
        <input required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <div className="field">
        <div className="field-head">
          <span>Текст (Markdown)</span>
          <div className="segmented segmented-sm">
            <button type="button" className={tab === "edit" ? "is-active" : ""} onClick={() => setTab("edit")}>
              Редактор
            </button>
            <button type="button" className={tab === "preview" ? "is-active" : ""} onClick={() => setTab("preview")}>
              Предпросмотр
            </button>
          </div>
        </div>
        {tab === "edit" ? (
          <textarea
            className="mono"
            rows={22}
            required
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
        ) : (
          <div className="preview">
            <MarkdownView source={content} />
          </div>
        )}
      </div>
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

export function LegalDocumentsPage() {
  usePageTitle("Документы");
  const pages = useApi(() => api.legal.list(), []);

  if (pages.error) return <ErrorMessage error={pages.error} onRetry={pages.reload} />;
  if (!pages.data) return <Spinner />;

  return (
    <section className="editor">
      <p className="muted">
        Документы открыты всем по ссылкам в подвале сайта. При регистрации ученик ставит галочку
        согласия — время согласия сохраняется в его учётной записи.
      </p>
      {pages.data.map((page) => (
        <DocumentForm
          key={page.slug}
          page={page}
          onSaved={(updated) =>
            pages.setData((list) => list?.map((item) => (item.slug === updated.slug ? updated : item)))
          }
        />
      ))}
    </section>
  );
}

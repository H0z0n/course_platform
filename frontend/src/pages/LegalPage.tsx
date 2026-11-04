import { useParams } from "react-router";
import { api } from "../api/endpoints";
import type { LegalSlug } from "../api/types";
import { MarkdownView } from "../components/LessonContent";
import { ErrorMessage, Spinner } from "../components/ui";
import { formatDate } from "../lib/format";
import { useApi } from "../lib/useApi";
import { usePageTitle } from "../site/SiteContext";
import { NotFoundPage } from "./NotFoundPage";

const SLUGS: LegalSlug[] = ["privacy", "consent"];

export function LegalPage() {
  const { slug = "" } = useParams();
  const known = SLUGS.includes(slug as LegalSlug);
  const page = useApi(
    () => (known ? api.legal.get(slug as LegalSlug) : Promise.resolve(null)),
    [slug],
  );
  usePageTitle(page.data?.title);

  if (!known) return <NotFoundPage />;
  if (page.error) return <div className="container"><ErrorMessage error={page.error} /></div>;
  if (!page.data) return <Spinner />;

  return (
    <article className="container legal">
      <h1>{page.data.title}</h1>
      {page.data.updated_at && (
        <p className="muted small">Обновлено {formatDate(page.data.updated_at)}</p>
      )}
      <MarkdownView source={page.data.content} />
    </article>
  );
}

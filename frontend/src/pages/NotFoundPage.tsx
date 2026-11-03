import { Link } from "react-router";
import { EmptyState } from "../components/ui";
import { usePageTitle } from "../site/SiteContext";

export function NotFoundPage() {
  usePageTitle("Страница не найдена");
  return (
    <div className="container">
      <EmptyState title="Страница не найдена">
        <Link to="/">Перейти в каталог курсов</Link>
      </EmptyState>
    </div>
  );
}

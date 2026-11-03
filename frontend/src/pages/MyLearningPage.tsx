import { Link } from "react-router";
import { api } from "../api/endpoints";
import { EmptyState, ErrorMessage, ProgressBar, Spinner } from "../components/ui";
import { formatDate } from "../lib/format";
import { useApi } from "../lib/useApi";
import { usePageTitle } from "../site/SiteContext";

export function MyLearningPage() {
  usePageTitle("Моё обучение");
  const courses = useApi(() => api.progress.mine(), []);
  const purchases = useApi(() => api.purchases.mine(), []);

  return (
    <div className="container">
      <h1>Моё обучение</h1>

      {courses.error && <ErrorMessage error={courses.error} onRetry={courses.reload} />}
      {!courses.data && !courses.error && <Spinner />}
      {courses.data?.length === 0 && (
        <EmptyState title="Вы ещё не начали ни одного курса">
          <Link to="/">Выберите курс в каталоге</Link> — первые уроки бесплатные.
        </EmptyState>
      )}
      {courses.data && courses.data.length > 0 && (
        <div className="my-grid">
          {courses.data.map((course) => (
            <Link key={course.course_id} to={`/courses/${course.slug}`} className="card my-course">
              <div className="my-course-head">
                <h3>{course.title}</h3>
                {!course.has_purchase && <span className="badge badge-free">Пробные уроки</span>}
              </div>
              <ProgressBar percent={course.percent} />
              <p className="muted small">
                {course.percent}% · пройдено {course.completed_lessons} из {course.total_lessons}
              </p>
            </Link>
          ))}
        </div>
      )}

      <h2>История покупок</h2>
      {purchases.error && <ErrorMessage error={purchases.error} onRetry={purchases.reload} />}
      {purchases.data?.length === 0 && <p className="muted">Покупок пока нет.</p>}
      {purchases.data && purchases.data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Что куплено</th>
                <th>Номер платежа</th>
              </tr>
            </thead>
            <tbody>
              {purchases.data.map((purchase) => (
                <tr key={purchase.id}>
                  <td>{formatDate(purchase.purchased_at)}</td>
                  <td>
                    <Link to={`/courses/${purchase.course_slug}`}>{purchase.course_title}</Link>
                    {purchase.module_title && (
                      <span className="muted"> · модуль «{purchase.module_title}»</span>
                    )}
                  </td>
                  <td className="mono small">{purchase.payment_reference}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

import { Link, useNavigate } from "react-router";
import { api } from "../../api/endpoints";
import { ChevronLeftIcon, PencilIcon, PlusIcon } from "../../components/Icons";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui";
import { formatPrice } from "../../lib/format";
import { useApi } from "../../lib/useApi";
import { usePageTitle, useSite } from "../../site/SiteContext";
import { CourseForm } from "./CourseForm";

export function AdminCoursesPage() {
  usePageTitle("Управление курсами");
  const { currency } = useSite();
  const courses = useApi(() => api.courses.list(), []);

  return (
    <section>
      <div className="section-head">
        <h2>Курсы</h2>
        <Link to="/admin/courses/new" className="btn btn-primary">
          <PlusIcon /> Новый курс
        </Link>
      </div>
      {courses.error && <ErrorMessage error={courses.error} onRetry={courses.reload} />}
      {!courses.data && !courses.error && <Spinner />}
      {courses.data?.length === 0 && (
        <EmptyState title="Курсов пока нет">Создайте первый курс кнопкой выше.</EmptyState>
      )}
      {courses.data && courses.data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Название</th>
                <th>Адрес</th>
                <th>Цена</th>
                <th aria-label="Действия" />
              </tr>
            </thead>
            <tbody>
              {courses.data.map((course) => (
                <tr key={course.id}>
                  <td>
                    <Link to={`/admin/courses/${course.id}`}>{course.title}</Link>
                  </td>
                  <td className="mono small">/courses/{course.slug}</td>
                  <td>
                    {course.price !== null ? (
                      formatPrice(course.price, currency)
                    ) : (
                      <span className="muted">по модулям</span>
                    )}
                  </td>
                  <td className="actions">
                    <Link to={`/admin/courses/${course.id}`} className="btn btn-sm">
                      <PencilIcon /> Редактировать
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function NewCoursePage() {
  usePageTitle("Новый курс");
  const navigate = useNavigate();
  return (
    <section className="editor">
      <Link to="/admin" className="back-link">
        <ChevronLeftIcon /> Все курсы
      </Link>
      <h2>Новый курс</h2>
      <CourseForm onSaved={(course) => navigate(`/admin/courses/${course.id}`, { replace: true })} />
    </section>
  );
}

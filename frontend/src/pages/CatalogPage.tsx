import { Link } from "react-router";
import { api } from "../api/endpoints";
import { isStaff, useAuth } from "../auth/AuthContext";
import { CourseCard } from "../components/CourseCard";
import { EmptyState, ErrorMessage, Spinner } from "../components/ui";
import { plural } from "../lib/format";
import { useApi } from "../lib/useApi";
import { usePageTitle } from "../site/SiteContext";

export function CatalogPage() {
  usePageTitle();
  const { user } = useAuth();
  const courses = useApi(() => api.courses.list(), []);
  const hasQuizzes = courses.data?.some((course) => course.question_count > 0) ?? false;

  return (
    <div className="container">
      <section className="hero">
        <div className="hero-text">
          <span className="hero-badge">Первые уроки — бесплатно</span>
          <h1>
            Учитесь в своём темпе —<br />
            глава за главой
          </h1>
          <p>
            {hasQuizzes
              ? "После уроков — короткие вопросы, чтобы проверить себя, и прогресс, который видно."
              : "Короткие понятные уроки и прогресс, который видно."}
          </p>
          <a href="#courses" className="btn btn-light btn-lg">
            Выбрать курс
          </a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <span className="shape shape-square" />
          <span className="shape shape-circle" />
          <span className="shape shape-arch" />
          <span className="shape shape-soft" />
        </div>
      </section>

      <section id="courses" className="catalog">
        <div className="section-head">
          <h2>Курсы</h2>
          {courses.data && (
            <span className="muted">{plural(courses.data.length, "курс", "курса", "курсов")}</span>
          )}
        </div>
        {courses.error && <ErrorMessage error={courses.error} onRetry={courses.reload} />}
        {!courses.data && !courses.error && <Spinner />}
        {courses.data?.length === 0 && (
          <EmptyState title="Курсов пока нет">
            {isStaff(user) ? <Link to="/admin/courses/new">Создайте первый курс</Link> : "Загляните чуть позже."}
          </EmptyState>
        )}
        {courses.data && courses.data.length > 0 && (
          <div className="course-grid">
            {courses.data.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

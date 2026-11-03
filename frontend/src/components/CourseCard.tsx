import { Link } from "react-router";
import type { Course, CourseCard as CourseCardData } from "../api/types";
import { coverColor, initials } from "../lib/cover";
import { excerpt, formatPrice, plural } from "../lib/format";
import { useSite } from "../site/SiteContext";

export function CourseCover({ course, size = "md" }: { course: Course; size?: "md" | "lg" }) {
  if (course.cover_image_url) {
    return <img className={`cover cover-${size}`} src={course.cover_image_url} alt="" loading="lazy" />;
  }
  return (
    <div className={`cover cover-${size}`} style={{ background: coverColor(course.slug) }} aria-hidden="true">
      <span>{initials(course.title)}</span>
    </div>
  );
}

export function CourseCard({ course }: { course: CourseCardData }) {
  const { currency } = useSite();
  return (
    <article className="course-card">
      <Link to={`/courses/${course.slug}`} className="course-card-cover" tabIndex={-1} aria-hidden="true">
        <CourseCover course={course} />
        {course.free_lesson_count > 0 && (
          <span className="cover-badge">
            {plural(course.free_lesson_count, "урок", "урока", "уроков")} бесплатно
          </span>
        )}
      </Link>
      <div className="course-card-body">
        <h3>
          <Link to={`/courses/${course.slug}`}>{course.title}</Link>
        </h3>
        {course.description && <p className="muted">{excerpt(course.description)}</p>}
        <ul className="chips" aria-label="О курсе">
          <li>{plural(course.module_count, "модуль", "модуля", "модулей")}</li>
          <li>{plural(course.lesson_count, "урок", "урока", "уроков")}</li>
          {course.question_count > 0 && <li>Вопросы для самопроверки</li>}
          {course.price === null && <li>По модулям</li>}
        </ul>
        <div className="course-card-footer">
          <span className="course-card-price">
            {course.price !== null ? formatPrice(course.price, currency) : ""}
          </span>
          <Link to={`/courses/${course.slug}`} className="btn btn-primary">
            Начать
          </Link>
        </div>
      </div>
    </article>
  );
}

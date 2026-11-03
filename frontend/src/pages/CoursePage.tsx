import { Link, useParams } from "react-router";
import { api } from "../api/endpoints";
import type { LessonProgress } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { CourseCover } from "../components/CourseCard";
import { CourseOutlineList } from "../components/CourseOutlineList";
import { ClockIcon } from "../components/Icons";
import { MarkdownView } from "../components/LessonContent";
import { PurchaseOptions } from "../components/PurchaseOptions";
import { ErrorMessage, ProgressBar, Spinner } from "../components/ui";
import { formatMinutes, plural, totalMinutes } from "../lib/format";
import { useApi } from "../lib/useApi";
import { usePageTitle } from "../site/SiteContext";

export function CoursePage() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const outline = useApi(() => api.courses.bySlug(slug), [slug, user?.id]);
  const courseId = outline.data?.id;
  const progress = useApi(
    () => (user && courseId ? api.courses.progress(courseId) : Promise.resolve(null)),
    [courseId, user?.id],
  );
  usePageTitle(outline.data?.title);

  if (outline.error) {
    return (
      <div className="container">
        <ErrorMessage error={outline.error} onRetry={outline.reload} />
      </div>
    );
  }
  const course = outline.data;
  if (!course) return <Spinner />;

  const progressMap = new Map<number, LessonProgress>(
    (progress.data?.lessons ?? []).map((row) => [row.lesson_id, row]),
  );
  const lessons = course.modules.flatMap((module) => module.lessons);
  const nextLesson =
    lessons.find((lesson) => lesson.is_open && !progressMap.get(lesson.id)?.completed) ??
    lessons.find((lesson) => lesson.is_open);
  const freeCount = lessons.filter((lesson) => lesson.is_free_preview).length;
  const minutes = totalMinutes(lessons);
  const started = (progress.data?.lessons.length ?? 0) > 0;

  const refresh = () => {
    outline.reload();
    progress.reload();
  };

  return (
    <div className="container">
      <section className="course-hero">
        <CourseCover course={course} size="lg" />
        <div className="course-hero-text">
          <p className="eyebrow">Курс</p>
          <h1>{course.title}</h1>
          <ul className="course-facts">
            <li>{plural(course.modules.length, "модуль", "модуля", "модулей")}</li>
            <li>{plural(lessons.length, "урок", "урока", "уроков")}</li>
            {freeCount > 0 && <li>{plural(freeCount, "бесплатный", "бесплатных", "бесплатных")}</li>}
            {minutes > 0 && (
              <li className="course-time">
                <ClockIcon /> {formatMinutes(minutes)}
              </li>
            )}
          </ul>
          {progress.data && progress.data.total_lessons > 0 && (
            <div className="course-progress">
              <ProgressBar percent={progress.data.percent} />
              <span className="muted small">
                Пройдено {progress.data.completed_lessons} из {progress.data.total_lessons}
              </span>
            </div>
          )}
          {nextLesson && (
            <Link to={`/courses/${course.slug}/lessons/${nextLesson.id}`} className="btn btn-primary btn-lg">
              {started ? "Продолжить обучение" : "Начать обучение"}
            </Link>
          )}
        </div>
      </section>

      <div className="course-layout">
        <div className="course-main">
          {course.description && (
            <section className="course-description">
              <MarkdownView source={course.description} />
            </section>
          )}
          <h2>Программа курса</h2>
          <CourseOutlineList course={course} progress={progressMap} />
        </div>
        <aside className="course-aside">
          <div className="card sticky">
            <h3>Доступ к курсу</h3>
            <PurchaseOptions course={course} onPurchased={refresh} />
          </div>
        </aside>
      </div>
    </div>
  );
}

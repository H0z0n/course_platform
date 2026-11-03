import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { toApiError } from "../api/client";
import { api } from "../api/endpoints";
import type { CourseOutline, LessonProgress } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { CourseOutlineList } from "../components/CourseOutlineList";
import { CheckIcon, ChevronLeftIcon, ChevronRightIcon, LockIcon } from "../components/Icons";
import { LessonContent } from "../components/LessonContent";
import { PurchaseOptions } from "../components/PurchaseOptions";
import { Quiz } from "../components/Quiz";
import { EmptyState, ErrorMessage, ProgressBar, Spinner } from "../components/ui";
import { formatMinutes } from "../lib/format";
import { useApi } from "../lib/useApi";
import { usePageTitle } from "../site/SiteContext";

function Paywall({
  course,
  moduleId,
  loggedIn,
  onPurchased,
}: {
  course: CourseOutline;
  moduleId: number;
  loggedIn: boolean;
  onPurchased: () => void;
}) {
  return (
    <div className="paywall card">
      <div className="paywall-icon">
        <LockIcon />
      </div>
      <h2>Этот урок пока закрыт</h2>
      <p className="muted">
        {loggedIn
          ? "Купите весь курс или модуль с этим уроком — доступ откроется сразу."
          : "Войдите в аккаунт, чтобы купить курс или модуль с этим уроком."}
      </p>
      <PurchaseOptions course={course} onlyModuleId={moduleId} onPurchased={onPurchased} />
    </div>
  );
}

export function LessonPage() {
  const { slug = "", lessonId = "" } = useParams();
  const id = Number(lessonId);
  const { user } = useAuth();
  const outline = useApi(() => api.courses.bySlug(slug), [slug, user?.id]);
  const lesson = useApi(() => api.lessons.get(id), [id, user?.id]);
  const courseId = outline.data?.id;
  const progress = useApi(
    () => (user && courseId ? api.courses.progress(courseId) : Promise.resolve(null)),
    [courseId, user?.id],
  );
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const course = outline.data;
  const lessons = course ? course.modules.flatMap((module) => module.lessons) : [];
  const index = lessons.findIndex((item) => item.id === id);
  const current = index >= 0 ? lessons[index] : undefined;
  const previous = index > 0 ? lessons[index - 1] : undefined;
  const next = index >= 0 ? lessons[index + 1] : undefined;
  const module = course?.modules.find((item) => item.lessons.some((entry) => entry.id === id));
  const progressMap = new Map<number, LessonProgress>(
    (progress.data?.lessons ?? []).map((row) => [row.lesson_id, row]),
  );
  const completed = progressMap.get(id)?.completed ?? false;
  usePageTitle(current?.title);

  useEffect(() => {
    window.scrollTo(0, 0);
    setActionError(null);
  }, [id]);

  useEffect(() => {
    if (!user || !lesson.data || !progress.data) return;
    const lessonIdToStart = lesson.data.id;
    if (progress.data.lessons.some((row) => row.lesson_id === lessonIdToStart)) return;
    api.lessons
      .start(lessonIdToStart)
      .then((row) =>
        progress.setData((state) => (state ? { ...state, lessons: [...state.lessons, row] } : state)),
      )
      .catch(() => undefined);
  }, [user, lesson.data, progress.data]);

  async function toggleCompleted() {
    setSaving(true);
    setActionError(null);
    try {
      await api.lessons.setCompleted(id, !completed);
      progress.reload();
    } catch (reason) {
      setActionError(toApiError(reason).message);
    } finally {
      setSaving(false);
    }
  }

  function refreshAfterPurchase() {
    outline.reload();
    lesson.reload();
    progress.reload();
  }

  if (outline.error) {
    return (
      <div className="container">
        <ErrorMessage error={outline.error} onRetry={outline.reload} />
      </div>
    );
  }
  if (!course) return <Spinner />;
  if (!current || !module) {
    return (
      <div className="container">
        <EmptyState title="Урок не найден">
          <Link to={`/courses/${course.slug}`}>Вернуться к курсу</Link>
        </EmptyState>
      </div>
    );
  }

  const locked = lesson.error?.status === 401 || lesson.error?.status === 403;

  return (
    <div className="container lesson-layout">
      <aside className="lesson-sidebar">
        <Link to={`/courses/${course.slug}`} className="back-link">
          ← {course.title}
        </Link>
        {progress.data && progress.data.total_lessons > 0 && (
          <div className="sidebar-progress">
            <ProgressBar percent={progress.data.percent} />
            <span className="muted small">
              Пройдено {progress.data.completed_lessons} из {progress.data.total_lessons} уроков
            </span>
          </div>
        )}
        <CourseOutlineList course={course} progress={progressMap} activeLessonId={id} compact />
      </aside>

      <article className="lesson-main">
        <p className="eyebrow">
          {module.title} · урок {module.lessons.findIndex((item) => item.id === id) + 1}
          {current.duration_minutes !== null && ` · ${formatMinutes(current.duration_minutes)}`}
        </p>
        <h1 className="lesson-title">{current.title}</h1>

        {locked && (
          <Paywall
            course={course}
            moduleId={module.id}
            loggedIn={user !== null}
            onPurchased={refreshAfterPurchase}
          />
        )}
        {lesson.error && !locked && <ErrorMessage error={lesson.error} onRetry={lesson.reload} />}
        {!lesson.data && !lesson.error && <Spinner />}

        {lesson.data && (
          <>
            <LessonContent
              contentType={lesson.data.content_type}
              content={lesson.data.content}
              title={lesson.data.title}
            />
            {current.question_count > 0 && <Quiz lessonId={id} canAnswer={user !== null} />}
            <div className="lesson-actions">
              {user ? (
                <button
                  type="button"
                  className={completed ? "btn btn-success" : "btn btn-primary"}
                  onClick={toggleCompleted}
                  disabled={saving || !progress.data}
                >
                  {completed ? (
                    <>
                      <CheckIcon /> Урок пройден
                    </>
                  ) : (
                    "Отметить урок пройденным"
                  )}
                </button>
              ) : (
                <p className="muted">
                  <Link to="/login" state={{ from: `/courses/${course.slug}/lessons/${id}` }}>
                    Войдите
                  </Link>
                  , чтобы сохранять прогресс.
                </p>
              )}
            </div>
            {actionError && <ErrorMessage error={actionError} />}
          </>
        )}

        <nav className="lesson-nav" aria-label="Соседние уроки">
          {previous ? (
            <Link to={`/courses/${course.slug}/lessons/${previous.id}`} className="lesson-nav-link">
              <ChevronLeftIcon />
              <span>
                <small className="muted">Предыдущий</small>
                {previous.title}
              </span>
            </Link>
          ) : (
            <span />
          )}
          {next && (
            <Link
              to={`/courses/${course.slug}/lessons/${next.id}`}
              className="lesson-nav-link lesson-nav-next"
            >
              <span>
                <small className="muted">Следующий</small>
                {next.title}
              </span>
              <ChevronRightIcon />
            </Link>
          )}
        </nav>
      </article>
    </div>
  );
}

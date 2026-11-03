import { Link } from "react-router";
import type { CourseOutline, LessonOutline, LessonProgress } from "../api/types";
import { formatMinutes, plural, roman, totalMinutes } from "../lib/format";
import { CheckIcon, LockIcon, PlayIcon, QuizIcon, TextIcon } from "./Icons";

function LessonIcon({ lesson, progress }: { lesson: LessonOutline; progress?: LessonProgress }) {
  if (progress?.completed) return <CheckIcon className="icon-done" />;
  if (!lesson.is_open) return <LockIcon className="icon-locked" />;
  return lesson.content_type === "video" ? <PlayIcon /> : <TextIcon />;
}

export function CourseOutlineList({
  course,
  progress,
  activeLessonId,
  compact = false,
}: {
  course: CourseOutline;
  progress?: Map<number, LessonProgress>;
  activeLessonId?: number;
  compact?: boolean;
}) {
  if (course.modules.length === 0) {
    return <p className="muted">Программа курса пока не опубликована.</p>;
  }

  return (
    <ol className={compact ? "outline outline-compact" : "outline"}>
      {course.modules.map((module, index) => {
        const minutes = totalMinutes(module.lessons);
        return (
          <li key={module.id} className="outline-module">
            <div className="outline-module-head">
              <span className="outline-module-title">
                {roman(index)}. {module.title}
              </span>
              {!compact && (
                <span className="outline-meta">
                  {plural(module.lessons.length, "урок", "урока", "уроков")}
                  {minutes > 0 && ` · ${formatMinutes(minutes)}`}
                </span>
              )}
              {module.is_purchased && <span className="badge badge-success">Куплен</span>}
            </div>
            <ol className="outline-lessons">
              {module.lessons.map((lesson) => {
                const state = progress?.get(lesson.id);
                const active = lesson.id === activeLessonId;
                const classes = [
                  "outline-lesson",
                  active ? "is-active" : "",
                  lesson.is_open ? "" : "is-locked",
                  state?.completed ? "is-done" : "",
                ];
                return (
                  <li key={lesson.id}>
                    <Link
                      to={`/courses/${course.slug}/lessons/${lesson.id}`}
                      className={classes.filter(Boolean).join(" ")}
                      aria-current={active ? "page" : undefined}
                    >
                      {!(compact && active) && <LessonIcon lesson={lesson} progress={state} />}
                      <span className="outline-lesson-title">{lesson.title}</span>
                      {!compact && (
                        <span className="outline-lesson-meta">
                          {lesson.is_free_preview && <span className="badge badge-free">Бесплатно</span>}
                          {lesson.question_count > 0 && (
                            <span className="outline-quiz" title="Есть вопросы для самопроверки">
                              <QuizIcon /> {lesson.question_count}
                            </span>
                          )}
                          {lesson.duration_minutes !== null && (
                            <span>{formatMinutes(lesson.duration_minutes)}</span>
                          )}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ol>
          </li>
        );
      })}
    </ol>
  );
}

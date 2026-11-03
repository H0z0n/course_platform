import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { ContentType, CourseOutline, ModuleOutline, ModulePayload } from "../../api/types";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  ChevronLeftIcon,
  PencilIcon,
  PlayIcon,
  PlusIcon,
  TextIcon,
  TrashIcon,
} from "../../components/Icons";
import { ErrorMessage, Spinner } from "../../components/ui";
import { formatMinutes, formatPrice, normalizePrice, plural } from "../../lib/format";
import { useApi } from "../../lib/useApi";
import { usePageTitle, useSite } from "../../site/SiteContext";
import { CourseForm } from "./CourseForm";

type Run = (action: () => Promise<unknown>) => Promise<boolean>;

function swap(ids: number[], index: number, delta: number): number[] {
  const result = [...ids];
  [result[index], result[index + delta]] = [result[index + delta], result[index]];
  return result;
}

function ModuleFields({
  initial,
  submitLabel,
  busy,
  onSubmit,
  onCancel,
}: {
  initial?: ModuleOutline;
  submitLabel: string;
  busy: boolean;
  onSubmit: (data: ModulePayload) => Promise<boolean>;
  onCancel?: () => void;
}) {
  const { currency } = useSite();
  const [title, setTitle] = useState(initial?.title ?? "");
  const [price, setPrice] = useState(initial?.price ?? "");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const succeeded = await onSubmit({ title, price: normalizePrice(price) });
    if (succeeded && !initial) {
      setTitle("");
      setPrice("");
    }
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      <input
        required
        maxLength={200}
        placeholder="Название модуля"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />
      <input
        className="input-price"
        inputMode="decimal"
        placeholder={`Цена, ${currency}`}
        title="Пусто — модуль отдельно не продаётся"
        value={price}
        onChange={(event) => setPrice(event.target.value)}
      />
      <button type="submit" className="btn btn-primary" disabled={busy}>
        {submitLabel}
      </button>
      {onCancel && (
        <button type="button" className="btn" onClick={onCancel}>
          Отмена
        </button>
      )}
    </form>
  );
}

function ModuleEditor({
  course,
  module,
  index,
  busy,
  run,
}: {
  course: CourseOutline;
  module: ModuleOutline;
  index: number;
  busy: boolean;
  run: Run;
}) {
  const { currency } = useSite();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonType, setLessonType] = useState<ContentType>("text");
  const moduleIds = course.modules.map((item) => item.id);
  const lessonIds = module.lessons.map((lesson) => lesson.id);

  async function addLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run(async () => {
      const lesson = await api.modules.createLesson(module.id, {
        title: lessonTitle,
        content_type: lessonType,
      });
      navigate(`/admin/courses/${course.id}/lessons/${lesson.id}`);
    });
  }

  return (
    <div className="card module-editor">
      <div className="module-editor-head">
        <span className="outline-index">{index + 1}</span>
        {editing ? (
          <ModuleFields
            initial={module}
            submitLabel="Сохранить"
            busy={busy}
            onCancel={() => setEditing(false)}
            onSubmit={async (data) => {
              const succeeded = await run(() => api.modules.update(module.id, data));
              if (succeeded) setEditing(false);
              return succeeded;
            }}
          />
        ) : (
          <>
            <div className="module-editor-title">
              <strong>{module.title}</strong>
              <span className="muted small">
                {module.price !== null
                  ? formatPrice(module.price, currency)
                  : "отдельно не продаётся"}
              </span>
            </div>
            <div className="icon-buttons">
              <button
                type="button"
                className="btn btn-icon"
                title="Выше"
                disabled={busy || index === 0}
                onClick={() =>
                  run(() => api.courses.reorderModules(course.id, swap(moduleIds, index, -1)))
                }
              >
                <ArrowUpIcon />
              </button>
              <button
                type="button"
                className="btn btn-icon"
                title="Ниже"
                disabled={busy || index === moduleIds.length - 1}
                onClick={() =>
                  run(() => api.courses.reorderModules(course.id, swap(moduleIds, index, 1)))
                }
              >
                <ArrowDownIcon />
              </button>
              <button
                type="button"
                className="btn btn-icon"
                title="Изменить"
                onClick={() => setEditing(true)}
              >
                <PencilIcon />
              </button>
              <button
                type="button"
                className="btn btn-icon btn-danger-ghost"
                title="Удалить модуль"
                disabled={busy}
                onClick={() => {
                  if (window.confirm(`Удалить модуль «${module.title}» со всеми уроками?`)) {
                    void run(() => api.modules.remove(module.id));
                  }
                }}
              >
                <TrashIcon />
              </button>
            </div>
          </>
        )}
      </div>

      <ol className="lesson-rows">
        {module.lessons.map((lesson, lessonIndex) => (
          <li key={lesson.id} className="lesson-row">
            <span className="lesson-row-icon">
              {lesson.content_type === "video" ? <PlayIcon /> : <TextIcon />}
            </span>
            <Link to={`/admin/courses/${course.id}/lessons/${lesson.id}`} className="lesson-row-title">
              {lesson.title}
            </Link>
            {lesson.is_free_preview && <span className="badge badge-free">Бесплатно</span>}
            {lesson.question_count > 0 && (
              <span className="muted small">{plural(lesson.question_count, "вопрос", "вопроса", "вопросов")}</span>
            )}
            {lesson.duration_minutes !== null && (
              <span className="muted small">{formatMinutes(lesson.duration_minutes)}</span>
            )}
            <div className="icon-buttons">
              <button
                type="button"
                className="btn btn-icon"
                title="Выше"
                disabled={busy || lessonIndex === 0}
                onClick={() =>
                  run(() => api.modules.reorderLessons(module.id, swap(lessonIds, lessonIndex, -1)))
                }
              >
                <ArrowUpIcon />
              </button>
              <button
                type="button"
                className="btn btn-icon"
                title="Ниже"
                disabled={busy || lessonIndex === lessonIds.length - 1}
                onClick={() =>
                  run(() => api.modules.reorderLessons(module.id, swap(lessonIds, lessonIndex, 1)))
                }
              >
                <ArrowDownIcon />
              </button>
              <button
                type="button"
                className="btn btn-icon btn-danger-ghost"
                title="Удалить урок"
                disabled={busy}
                onClick={() => {
                  if (window.confirm(`Удалить урок «${lesson.title}»?`)) {
                    void run(() => api.lessons.remove(lesson.id));
                  }
                }}
              >
                <TrashIcon />
              </button>
            </div>
          </li>
        ))}
        {module.lessons.length === 0 && <li className="muted small">В модуле пока нет уроков.</li>}
      </ol>

      <form className="inline-form" onSubmit={addLesson}>
        <input
          required
          maxLength={200}
          placeholder="Название нового урока"
          value={lessonTitle}
          onChange={(event) => setLessonTitle(event.target.value)}
        />
        <select
          value={lessonType}
          onChange={(event) => setLessonType(event.target.value as ContentType)}
          aria-label="Тип урока"
        >
          <option value="text">Текст</option>
          <option value="video">Видео</option>
        </select>
        <button type="submit" className="btn" disabled={busy}>
          <PlusIcon /> Урок
        </button>
      </form>
    </div>
  );
}

export function CourseEditorPage() {
  const { courseId = "" } = useParams();
  const id = Number(courseId);
  const navigate = useNavigate();
  const outline = useApi(() => api.courses.get(id), [id]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  usePageTitle(outline.data ? `Редактор: ${outline.data.title}` : "Редактор курса");

  const run: Run = async (action) => {
    setBusy(true);
    setError(null);
    try {
      await action();
      outline.reload();
      return true;
    } catch (reason) {
      setError(toApiError(reason).message);
      return false;
    } finally {
      setBusy(false);
    }
  };

  if (outline.error) return <ErrorMessage error={outline.error} onRetry={outline.reload} />;
  const course = outline.data;
  if (!course) return <Spinner />;

  async function removeCourse() {
    if (!course || !window.confirm(`Удалить курс «${course.title}» целиком?`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.courses.remove(course.id);
      navigate("/admin", { replace: true });
    } catch (reason) {
      setError(toApiError(reason).message);
      setBusy(false);
    }
  }

  return (
    <section className="editor">
      <div className="editor-head">
        <Link to="/admin" className="back-link">
          <ChevronLeftIcon /> Все курсы
        </Link>
        <Link to={`/courses/${course.slug}`} className="btn btn-ghost btn-sm">
          Открыть на сайте
        </Link>
      </div>

      <CourseForm initial={course} onSaved={() => outline.reload()} />

      <div className="section-head">
        <h2>Модули и уроки</h2>
      </div>
      {error && <ErrorMessage error={error} />}
      {course.modules.map((module, index) => (
        <ModuleEditor
          key={module.id}
          course={course}
          module={module}
          index={index}
          busy={busy}
          run={run}
        />
      ))}
      <div className="card">
        <h3>Новый модуль</h3>
        <ModuleFields
          submitLabel="Добавить модуль"
          busy={busy}
          onSubmit={(data) => run(() => api.courses.createModule(course.id, data))}
        />
      </div>

      <div className="card danger-zone">
        <h3>Удаление курса</h3>
        <p className="muted">
          Курс удалится вместе с модулями, уроками и прогрессом учеников. Если курс или его модули
          уже покупали, сервер не даст его удалить.
        </p>
        <button type="button" className="btn btn-danger" disabled={busy} onClick={removeCourse}>
          <TrashIcon /> Удалить курс
        </button>
      </div>
    </section>
  );
}

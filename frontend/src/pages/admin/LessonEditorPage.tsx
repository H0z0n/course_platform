import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { ContentType, CourseOutline, Lesson } from "../../api/types";
import { CheckIcon, ChevronLeftIcon, PlayIcon, TextIcon, TrashIcon } from "../../components/Icons";
import { MarkdownView, VideoPlayer } from "../../components/LessonContent";
import { ErrorMessage, Spinner } from "../../components/ui";
import { useApi } from "../../lib/useApi";
import { usePageTitle } from "../../site/SiteContext";
import { QuizEditor } from "./QuizEditor";

function LessonForm({
  course,
  lesson,
  onSaved,
}: {
  course: CourseOutline;
  lesson: Lesson;
  onSaved: (lesson: Lesson) => void;
}) {
  const navigate = useNavigate();
  const [title, setTitle] = useState(lesson.title);
  const [moduleId, setModuleId] = useState(lesson.module_id);
  const [contentType, setContentType] = useState<ContentType>(lesson.content_type);
  const [text, setText] = useState(lesson.content_type === "text" ? lesson.content : "");
  const [videoUrl, setVideoUrl] = useState(lesson.content_type === "video" ? lesson.content : "");
  const [isFree, setIsFree] = useState(lesson.is_free_preview);
  const [duration, setDuration] = useState(lesson.duration_minutes?.toString() ?? "");
  const [tab, setTab] = useState<"edit" | "preview">("edit");
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.lessons.update(lesson.id, {
        title,
        module_id: moduleId,
        content_type: contentType,
        content: contentType === "text" ? text : videoUrl.trim(),
        is_free_preview: isFree,
        duration_minutes: duration.trim() ? Number(duration) : null,
      });
      onSaved(updated);
      setSaved(true);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Удалить урок «${lesson.title}»?`)) return;
    try {
      await api.lessons.remove(lesson.id);
      navigate(`/admin/courses/${course.id}`, { replace: true });
    } catch (reason) {
      setError(toApiError(reason).message);
    }
  }

  return (
    <form className="editor" onSubmit={save}>
      <div className="editor-head">
        <Link to={`/admin/courses/${course.id}`} className="back-link">
          <ChevronLeftIcon /> {course.title}
        </Link>
        <Link to={`/courses/${course.slug}/lessons/${lesson.id}`} className="btn btn-ghost btn-sm">
          Открыть на сайте
        </Link>
      </div>

      <div className="card form">
        <label className="field">
          <span>Название урока</span>
          <input
            required
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>

        <div className="form-row">
          <label className="field">
            <span>Модуль</span>
            <select value={moduleId} onChange={(event) => setModuleId(Number(event.target.value))}>
              {course.modules.map((module) => (
                <option key={module.id} value={module.id}>
                  {module.title}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Примерное время, мин</span>
            <input
              type="number"
              min={1}
              max={1000}
              placeholder="Например, 15"
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
            />
          </label>
          <div className="field">
            <span>Тип урока</span>
            <div className="segmented" role="group" aria-label="Тип урока">
              <button
                type="button"
                className={contentType === "text" ? "is-active" : ""}
                onClick={() => setContentType("text")}
              >
                <TextIcon /> Текст
              </button>
              <button
                type="button"
                className={contentType === "video" ? "is-active" : ""}
                onClick={() => setContentType("video")}
              >
                <PlayIcon /> Видео
              </button>
            </div>
          </div>
        </div>

        {contentType === "text" ? (
          <div className="field">
            <div className="field-head">
              <span>Текст урока (Markdown)</span>
              <div className="segmented segmented-sm">
                <button
                  type="button"
                  className={tab === "edit" ? "is-active" : ""}
                  onClick={() => setTab("edit")}
                >
                  Редактор
                </button>
                <button
                  type="button"
                  className={tab === "preview" ? "is-active" : ""}
                  onClick={() => setTab("preview")}
                >
                  Предпросмотр
                </button>
              </div>
            </div>
            {tab === "edit" ? (
              <textarea
                className="mono"
                rows={18}
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            ) : (
              <div className="preview">
                {text.trim() ? <MarkdownView source={text} /> : <p className="muted">Пока пусто.</p>}
              </div>
            )}
            <small className="muted">
              Заголовки — #, списки — «-», **жирный**, `код`, блоки кода через ```, таблицы.
            </small>
          </div>
        ) : (
          <div className="field">
            <label className="field">
              <span>Ссылка на видео</span>
              <input
                type="url"
                placeholder="https://youtu.be/… или https://example.com/video.mp4"
                value={videoUrl}
                onChange={(event) => setVideoUrl(event.target.value)}
              />
            </label>
            <small className="muted">
              Kinescope, VK Видео, Rutube, YouTube, Vimeo или прямая ссылка на файл .mp4 / .webm.
              Для учеников из России надёжнее Kinescope, VK Видео или Rutube.
            </small>
            {videoUrl.trim() && <VideoPlayer url={videoUrl} title={title} />}
          </div>
        )}

        <label className="checkbox">
          <input
            type="checkbox"
            checked={isFree}
            onChange={(event) => setIsFree(event.target.checked)}
          />
          <span>Бесплатный предпросмотр — урок открыт всем, даже без входа</span>
        </label>

        {error && <ErrorMessage error={error} />}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Сохраняем…" : "Сохранить"}
          </button>
          {saved && (
            <span className="saved">
              <CheckIcon /> Сохранено
            </span>
          )}
          <button type="button" className="btn btn-danger-ghost push-right" onClick={remove}>
            <TrashIcon /> Удалить урок
          </button>
        </div>
      </div>
    </form>
  );
}

export function LessonEditorPage() {
  const { courseId = "", lessonId = "" } = useParams();
  const outline = useApi(() => api.courses.get(Number(courseId)), [courseId]);
  const lesson = useApi(() => api.lessons.get(Number(lessonId)), [lessonId]);
  usePageTitle(lesson.data ? `Урок: ${lesson.data.title}` : "Редактор урока");

  const error = outline.error ?? lesson.error;
  if (error) return <ErrorMessage error={error} />;
  if (!outline.data || !lesson.data) return <Spinner />;

  return (
    <div className="editor">
      <LessonForm
        key={lesson.data.id}
        course={outline.data}
        lesson={lesson.data}
        onSaved={(updated) => lesson.setData(() => updated)}
      />
      <QuizEditor lessonId={lesson.data.id} />
    </div>
  );
}

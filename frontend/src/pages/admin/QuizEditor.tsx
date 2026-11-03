import { useState, type FormEvent } from "react";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { QuestionAdmin, QuestionKind, QuestionPayload } from "../../api/types";
import { ArrowDownIcon, ArrowUpIcon, CheckIcon, PencilIcon, PlusIcon, TrashIcon, XIcon } from "../../components/Icons";
import { ErrorMessage, Spinner } from "../../components/ui";
import { useApi } from "../../lib/useApi";

const KIND_LABELS: Record<QuestionKind, string> = {
  single: "Один вариант",
  multiple: "Несколько вариантов",
  text: "Короткий ответ",
};

interface OptionDraft {
  text: string;
  is_correct: boolean;
}

function emptyOptions(kind: QuestionKind): OptionDraft[] {
  if (kind === "text") return [{ text: "", is_correct: true }];
  return [
    { text: "", is_correct: true },
    { text: "", is_correct: false },
    { text: "", is_correct: false },
  ];
}

function QuestionForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: QuestionAdmin;
  onSave: (data: QuestionPayload) => Promise<boolean>;
  onCancel: () => void;
}) {
  const [kind, setKind] = useState<QuestionKind>(initial?.kind ?? "single");
  const [prompt, setPrompt] = useState(initial?.prompt ?? "");
  const [explanation, setExplanation] = useState(initial?.explanation ?? "");
  const [options, setOptions] = useState<OptionDraft[]>(
    initial?.options.map(({ text, is_correct }) => ({ text, is_correct })) ?? emptyOptions("single"),
  );
  const [pending, setPending] = useState(false);

  function changeKind(next: QuestionKind) {
    setKind(next);
    if (next === "text") {
      setOptions((current) => current.filter((o) => o.is_correct).map((o) => ({ ...o, is_correct: true })));
      return;
    }
    if (next === "single") {
      setOptions((current) => {
        const firstCorrect = current.findIndex((o) => o.is_correct);
        return current.map((o, index) => ({ ...o, is_correct: index === Math.max(firstCorrect, 0) }));
      });
    }
  }

  function updateOption(index: number, patch: Partial<OptionDraft>) {
    setOptions((current) =>
      current.map((option, i) => {
        if (kind === "single" && patch.is_correct) return { ...option, is_correct: i === index };
        return i === index ? { ...option, ...patch } : option;
      }),
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    const filled = options.filter((option) => option.text.trim() !== "");
    const saved = await onSave({ kind, prompt, explanation, options: filled });
    if (!saved) setPending(false);
  }

  return (
    <form className="question-form" onSubmit={submit}>
      <div className="segmented" role="group" aria-label="Тип вопроса">
        {(Object.keys(KIND_LABELS) as QuestionKind[]).map((value) => (
          <button
            key={value}
            type="button"
            className={kind === value ? "is-active" : ""}
            onClick={() => changeKind(value)}
          >
            {KIND_LABELS[value]}
          </button>
        ))}
      </div>
      <label className="field">
        <span>Вопрос (Markdown)</span>
        <textarea rows={3} required value={prompt} onChange={(event) => setPrompt(event.target.value)} />
      </label>
      <fieldset className="field option-drafts">
        <legend>{kind === "text" ? "Допустимые ответы" : "Варианты — отметьте правильные"}</legend>
        {options.map((option, index) => (
          <div key={index} className="option-draft">
            {kind !== "text" && (
              <input
                type={kind === "single" ? "radio" : "checkbox"}
                name="correct-option"
                aria-label="Правильный вариант"
                checked={option.is_correct}
                onChange={(event) => updateOption(index, { is_correct: event.target.checked })}
              />
            )}
            <input
              aria-label={kind === "text" ? "Допустимый ответ" : "Текст варианта"}
              placeholder={kind === "text" ? "Например: bool" : `Вариант ${index + 1}`}
              maxLength={500}
              value={option.text}
              onChange={(event) => updateOption(index, { text: event.target.value })}
            />
            <button
              type="button"
              className="btn btn-icon btn-danger-ghost"
              aria-label="Убрать вариант"
              disabled={options.length <= 1}
              onClick={() => setOptions((current) => current.filter((_, i) => i !== index))}
            >
              <XIcon />
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-sm btn-ghost add-option"
          onClick={() => setOptions((current) => [...current, { text: "", is_correct: kind === "text" }])}
        >
          <PlusIcon /> {kind === "text" ? "Ещё один допустимый ответ" : "Добавить вариант"}
        </button>
        {kind === "text" && (
          <small className="muted">Регистр и лишние пробелы при проверке не учитываются.</small>
        )}
      </fieldset>
      <label className="field">
        <span>Пояснение после ответа (необязательно)</span>
        <textarea rows={2} value={explanation} onChange={(event) => setExplanation(event.target.value)} />
      </label>
      {initial && <p className="muted small">После сохранения ответы учеников на этот вопрос сбросятся.</p>}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Сохраняем…" : "Сохранить вопрос"}
        </button>
        <button type="button" className="btn" onClick={onCancel}>
          Отмена
        </button>
      </div>
    </form>
  );
}

export function QuizEditor({ lessonId }: { lessonId: number }) {
  const questions = useApi(() => api.quiz.manage(lessonId), [lessonId]);
  const [editingId, setEditingId] = useState<number | "new" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    try {
      await action();
      questions.reload();
      return true;
    } catch (reason) {
      setError(toApiError(reason).message);
      return false;
    }
  }

  async function save(data: QuestionPayload, id?: number): Promise<boolean> {
    const saved = await run(() => (id ? api.quiz.replace(id, data) : api.quiz.create(lessonId, data)));
    if (saved) setEditingId(null);
    return saved;
  }

  const list = questions.data ?? [];
  const ids = list.map((question) => question.id);

  function move(index: number, delta: number) {
    const next = [...ids];
    [next[index], next[index + delta]] = [next[index + delta], next[index]];
    void run(() => api.quiz.reorder(lessonId, next));
  }

  return (
    <section className="card quiz-editor">
      <div className="section-head">
        <h2>Вопросы для самопроверки</h2>
        {editingId === null && (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => setEditingId("new")}>
            <PlusIcon /> Добавить вопрос
          </button>
        )}
      </div>
      {questions.error && <ErrorMessage error={questions.error} onRetry={questions.reload} />}
      {!questions.data && !questions.error && <Spinner />}
      {error && <ErrorMessage error={error} />}
      {questions.data?.length === 0 && editingId !== "new" && (
        <p className="muted">Вопросов пока нет. Они появятся под текстом урока в блоке «Проверьте себя».</p>
      )}

      <ol className="question-list">
        {list.map((question, index) => (
          <li key={question.id} className="question-item">
            {editingId === question.id ? (
              <QuestionForm
                initial={question}
                onSave={(data) => save(data, question.id)}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <>
                <div className="question-item-head">
                  <span className="quiz-kind">
                    {index + 1} · {KIND_LABELS[question.kind]}
                  </span>
                  <div className="icon-buttons">
                    <button type="button" className="btn btn-icon" aria-label="Выше" disabled={index === 0} onClick={() => move(index, -1)}>
                      <ArrowUpIcon />
                    </button>
                    <button type="button" className="btn btn-icon" aria-label="Ниже" disabled={index === list.length - 1} onClick={() => move(index, 1)}>
                      <ArrowDownIcon />
                    </button>
                    <button type="button" className="btn btn-icon" aria-label="Изменить" onClick={() => setEditingId(question.id)}>
                      <PencilIcon />
                    </button>
                    <button
                      type="button"
                      className="btn btn-icon btn-danger-ghost"
                      aria-label="Удалить вопрос"
                      onClick={() => {
                        if (window.confirm("Удалить вопрос вместе с ответами учеников?")) {
                          void run(() => api.quiz.remove(question.id));
                        }
                      }}
                    >
                      <TrashIcon />
                    </button>
                  </div>
                </div>
                <p className="question-item-prompt">{question.prompt}</p>
                <ul className="question-item-options">
                  {question.options.map((option) => (
                    <li key={option.id} className={option.is_correct ? "is-correct" : ""}>
                      {option.is_correct ? <CheckIcon /> : <span className="dot" aria-hidden="true" />}
                      {option.text}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </li>
        ))}
      </ol>
      {editingId === "new" && <QuestionForm onSave={(data) => save(data)} onCancel={() => setEditingId(null)} />}
    </section>
  );
}

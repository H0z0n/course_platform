import { useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router";
import { toApiError } from "../api/client";
import { api } from "../api/endpoints";
import type { AnswerResult, QuestionKind, QuestionPublic } from "../api/types";
import { useApi } from "../lib/useApi";
import { CheckIcon, XIcon } from "./Icons";
import { MarkdownView } from "./LessonContent";
import { ErrorMessage } from "./ui";

const KIND_LABELS: Record<QuestionKind, string> = {
  single: "один вариант",
  multiple: "несколько вариантов",
  text: "короткий ответ",
};

type OptionState = "correct" | "wrong" | "missed";

function optionState(optionId: number, result: AnswerResult | null): OptionState | null {
  if (result === null) return null;
  const selected = result.option_ids.includes(optionId);
  const correct = result.correct_option_ids.includes(optionId);
  if (selected) return correct ? "correct" : "wrong";
  if (correct && !result.is_correct) return "missed";
  return null;
}

function StatusLabel({ state }: { state: OptionState }) {
  if (state === "correct") {
    return (
      <span className="quiz-status">
        <CheckIcon /> Верно
      </span>
    );
  }
  if (state === "wrong") {
    return (
      <span className="quiz-status">
        <XIcon /> Неверно
      </span>
    );
  }
  return <span className="quiz-status">Правильный ответ</span>;
}

function QuestionCard({
  question,
  index,
  canAnswer,
  onAnswered,
}: {
  question: QuestionPublic;
  index: number;
  canAnswer: boolean;
  onAnswered: (result: AnswerResult) => void;
}) {
  const [editing, setEditing] = useState(question.result === null);
  const [selected, setSelected] = useState<number[]>(question.result?.option_ids ?? []);
  const [text, setText] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const result = editing ? null : question.result;
  const isText = question.kind === "text";
  const ready = isText ? text.trim() !== "" : selected.length > 0;

  function toggle(optionId: number) {
    if (question.kind === "single") {
      setSelected([optionId]);
      return;
    }
    setSelected((current) =>
      current.includes(optionId) ? current.filter((id) => id !== optionId) : [...current, optionId],
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const answer = await api.quiz.answer(
        question.id,
        isText ? { text } : { option_ids: selected },
      );
      onAnswered(answer);
      setEditing(false);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  function retry() {
    setSelected([]);
    setText("");
    setError(null);
    setEditing(true);
  }

  return (
    <form className="quiz-question" onSubmit={submit}>
      <p className="quiz-kind">
        Вопрос {index + 1} · {KIND_LABELS[question.kind]}
      </p>
      <div className="quiz-prompt">
        <MarkdownView source={question.prompt} />
      </div>

      {!isText && (
        <fieldset className="quiz-options" disabled={!editing || !canAnswer || pending}>
          <legend className="visually-hidden">Варианты ответа</legend>
          {question.options.map((option) => {
            const state = optionState(option.id, result);
            const checked = result ? result.option_ids.includes(option.id) : selected.includes(option.id);
            const classes = ["quiz-option", state ? `is-${state}` : "", checked && !result ? "is-selected" : ""];
            return (
              <label key={option.id} className={classes.filter(Boolean).join(" ")}>
                <input
                  type={question.kind === "single" ? "radio" : "checkbox"}
                  name={`question-${question.id}`}
                  checked={checked}
                  onChange={() => toggle(option.id)}
                />
                <span className="quiz-option-text">{option.text}</span>
                {state && <StatusLabel state={state} />}
              </label>
            );
          })}
        </fieldset>
      )}

      {isText && result && (
        <div className={`quiz-option ${result.is_correct ? "is-correct" : "is-wrong"}`}>
          <span className="quiz-option-text">{result.text}</span>
          <StatusLabel state={result.is_correct ? "correct" : "wrong"} />
        </div>
      )}
      {isText && !result && (
        <input
          className="quiz-input"
          aria-label="Ваш ответ"
          placeholder="Ваш ответ"
          maxLength={500}
          value={text}
          disabled={!canAnswer || pending}
          onChange={(event) => setText(event.target.value)}
        />
      )}

      {result && (!result.is_correct || result.explanation) && (
        <div className={result.is_correct ? "quiz-explanation" : "quiz-explanation is-wrong"}>
          {!result.is_correct && <p className="quiz-verdict">Не совсем.</p>}
          {isText && !result.is_correct && (
            <p>Правильный ответ: {result.accepted_answers.join(" или ")}</p>
          )}
          {result.explanation && <MarkdownView source={result.explanation} />}
        </div>
      )}
      {error && <ErrorMessage error={error} />}

      {canAnswer && (
        <div className="quiz-actions">
          {editing ? (
            <button type="submit" className="btn btn-primary" disabled={pending || !ready}>
              {pending ? "Проверяем…" : "Проверить"}
            </button>
          ) : (
            <button type="button" className="btn btn-outline" onClick={retry}>
              Ответить ещё раз
            </button>
          )}
        </div>
      )}
    </form>
  );
}

export function Quiz({ lessonId, canAnswer }: { lessonId: number; canAnswer: boolean }) {
  const location = useLocation();
  const questions = useApi(() => api.quiz.forLesson(lessonId), [lessonId, canAnswer]);

  if (questions.error) return <ErrorMessage error={questions.error} onRetry={questions.reload} />;
  if (!questions.data || questions.data.length === 0) return null;

  const results = questions.data.flatMap((question) => (question.result ? [question.result] : []));
  const correct = results.filter((result) => result.is_correct).length;

  function update(result: AnswerResult) {
    questions.setData((list) =>
      list?.map((question) => (question.id === result.question_id ? { ...question, result } : question)),
    );
  }

  return (
    <section className="quiz" aria-labelledby="quiz-title">
      <div className="quiz-head">
        <h2 id="quiz-title">Проверьте себя</h2>
        {canAnswer && (
          <span className="quiz-score">
            Отвечено {results.length} из {questions.data.length} · верно {correct}
          </span>
        )}
      </div>
      {!canAnswer && (
        <p className="muted">
          <Link to="/login" state={{ from: location.pathname }}>
            Войдите
          </Link>
          , чтобы отвечать на вопросы и видеть пояснения.
        </p>
      )}
      {questions.data.map((question, index) => (
        <QuestionCard
          key={question.id}
          question={question}
          index={index}
          canAnswer={canAnswer}
          onAnswered={update}
        />
      ))}
    </section>
  );
}

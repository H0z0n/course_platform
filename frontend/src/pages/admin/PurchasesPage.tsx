import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { Course, Purchase, PurchaseTarget } from "../../api/types";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { useApi } from "../../lib/useApi";
import { usePageTitle } from "../../site/SiteContext";

function GrantForm({ courses, onGranted }: { courses: Course[]; onGranted: () => void }) {
  const [email, setEmail] = useState("");
  const [courseId, setCourseId] = useState(0);
  const [target, setTarget] = useState("course");
  const [reference, setReference] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const outline = useApi(
    () => (courseId ? api.courses.get(courseId) : Promise.resolve(null)),
    [courseId],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setDone(null);
    const purchaseTarget: PurchaseTarget =
      target === "course" ? { course_id: courseId } : { module_id: Number(target) };
    try {
      const purchase = await api.purchases.grant({
        ...purchaseTarget,
        user_email: email,
        ...(reference.trim() ? { payment_reference: reference.trim() } : {}),
      });
      setDone(`Доступ выдан: ${purchase.user_email}`);
      setEmail("");
      setReference("");
      onGranted();
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h3>Выдать доступ вручную</h3>
      <p className="muted small">
        Например, если ученик оплатил по счёту или это подарок. Цена при выдаче не проверяется.
      </p>
      <div className="form-row">
        <label className="field">
          <span>Email ученика</span>
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Курс</span>
          <select
            required
            value={courseId || ""}
            onChange={(event) => {
              setCourseId(Number(event.target.value));
              setTarget("course");
            }}
          >
            <option value="" disabled>
              Выберите курс
            </option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="form-row">
        <label className="field">
          <span>Что открыть</span>
          <select
            value={target}
            onChange={(event) => setTarget(event.target.value)}
            disabled={!outline.data}
          >
            <option value="course">Весь курс</option>
            {outline.data?.modules.map((module) => (
              <option key={module.id} value={String(module.id)}>
                Модуль «{module.title}»
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Номер платежа (необязательно)</span>
          <input
            maxLength={255}
            placeholder="Например, счёт № 42"
            value={reference}
            onChange={(event) => setReference(event.target.value)}
          />
        </label>
      </div>
      {error && <ErrorMessage error={error} />}
      {done && <div className="alert alert-success">{done}</div>}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={pending || !courseId}>
          {pending ? "Выдаём…" : "Выдать доступ"}
        </button>
      </div>
    </form>
  );
}

export function PurchasesPage() {
  usePageTitle("Покупки");
  const purchases = useApi(() => api.purchases.list(), []);
  const courses = useApi(() => api.courses.list(), []);
  const [error, setError] = useState<string | null>(null);

  async function revoke(purchase: Purchase) {
    const item = purchase.module_title ?? purchase.course_title;
    if (!window.confirm(`Отозвать у ${purchase.user_email} доступ к «${item}»?`)) return;
    setError(null);
    try {
      await api.purchases.revoke(purchase.id);
      purchases.reload();
    } catch (reason) {
      setError(toApiError(reason).message);
    }
  }

  return (
    <section>
      <GrantForm courses={courses.data ?? []} onGranted={purchases.reload} />

      <div className="section-head">
        <h2>Все покупки</h2>
      </div>
      {error && <ErrorMessage error={error} />}
      {purchases.error && <ErrorMessage error={purchases.error} onRetry={purchases.reload} />}
      {!purchases.data && !purchases.error && <Spinner />}
      {purchases.data?.length === 0 && <EmptyState title="Покупок пока нет" />}
      {purchases.data && purchases.data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Ученик</th>
                <th>Что куплено</th>
                <th>Номер платежа</th>
                <th aria-label="Действия" />
              </tr>
            </thead>
            <tbody>
              {purchases.data.map((purchase) => (
                <tr key={purchase.id}>
                  <td className="nowrap">{formatDate(purchase.purchased_at)}</td>
                  <td>{purchase.user_email}</td>
                  <td>
                    <Link to={`/courses/${purchase.course_slug}`}>{purchase.course_title}</Link>
                    {purchase.module_title && (
                      <span className="muted"> · модуль «{purchase.module_title}»</span>
                    )}
                  </td>
                  <td className="mono small">{purchase.payment_reference}</td>
                  <td className="actions">
                    <button
                      type="button"
                      className="btn btn-sm btn-danger-ghost"
                      onClick={() => revoke(purchase)}
                    >
                      Отозвать
                    </button>
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

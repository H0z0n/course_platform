import { useState, type FormEvent } from "react";
import { toApiError } from "../../api/client";
import { api } from "../../api/endpoints";
import type { User, UserRole } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";
import { EmptyState, ErrorMessage, Spinner } from "../../components/ui";
import { useApi } from "../../lib/useApi";
import { usePageTitle } from "../../site/SiteContext";

const ROLE_LABELS: Record<UserRole, string> = {
  owner: "Владелец",
  admin: "Администратор",
  student: "Ученик",
};

export function UsersPage() {
  usePageTitle("Пользователи");
  const { user: me } = useAuth();
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const users = useApi(() => api.users.list(search), [search]);
  const [error, setError] = useState<string | null>(null);
  const canChangeRoles = me?.role === "owner";

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearch(query.trim());
  }

  async function changeRole(user: User, role: UserRole) {
    setError(null);
    try {
      const updated = await api.users.setRole(user.id, role);
      users.setData((list) => list?.map((item) => (item.id === updated.id ? updated : item)));
    } catch (reason) {
      setError(toApiError(reason).message);
    }
  }

  return (
    <section>
      <form className="search-form" onSubmit={submit} role="search">
        <input
          type="search"
          placeholder="Поиск по email"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" className="btn">
          Найти
        </button>
      </form>
      {!canChangeRoles && (
        <p className="muted small">Менять роли может только владелец платформы.</p>
      )}
      {error && <ErrorMessage error={error} />}
      {users.error && <ErrorMessage error={users.error} onRetry={users.reload} />}
      {!users.data && !users.error && <Spinner />}
      {users.data?.length === 0 && <EmptyState title="Никого не нашли" />}
      {users.data && users.data.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Роль</th>
              </tr>
            </thead>
            <tbody>
              {users.data.map((user) => (
                <tr key={user.id}>
                  <td>{user.email}</td>
                  <td>
                    {canChangeRoles && user.role !== "owner" ? (
                      <select
                        value={user.role}
                        onChange={(event) => changeRole(user, event.target.value as UserRole)}
                        aria-label={`Роль ${user.email}`}
                      >
                        <option value="student">{ROLE_LABELS.student}</option>
                        <option value="admin">{ROLE_LABELS.admin}</option>
                      </select>
                    ) : (
                      <span className={`badge role-${user.role}`}>{ROLE_LABELS[user.role]}</span>
                    )}
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

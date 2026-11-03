import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation } from "react-router";
import { toApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorMessage } from "../components/ui";
import { usePageTitle } from "../site/SiteContext";

function useRedirectTarget(): string {
  const location = useLocation();
  return (location.state as { from?: string } | null)?.from ?? "/";
}

function AuthForm({ mode }: { mode: "login" | "register" }) {
  const isLogin = mode === "login";
  usePageTitle(isLogin ? "Вход" : "Регистрация");
  const { user, login, register } = useAuth();
  const location = useLocation();
  const target = useRedirectTarget();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (user) return <Navigate to={target} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await (isLogin ? login(email, password) : register(email, password));
    } catch (reason) {
      setError(toApiError(reason).message);
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>{isLogin ? "Вход" : "Регистрация"}</h1>
        <label className="field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Пароль</span>
          <input
            type="password"
            autoComplete={isLogin ? "current-password" : "new-password"}
            required
            minLength={isLogin ? undefined : 8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {!isLogin && <small className="muted">Не короче 8 символов</small>}
        </label>
        {error && <ErrorMessage error={error} />}
        <button type="submit" className="btn btn-primary btn-block" disabled={pending}>
          {pending ? "Подождите…" : isLogin ? "Войти" : "Создать аккаунт"}
        </button>
        <p className="muted center">
          {isLogin ? "Нет аккаунта? " : "Уже есть аккаунт? "}
          <Link to={isLogin ? "/register" : "/login"} state={location.state}>
            {isLogin ? "Зарегистрируйтесь" : "Войдите"}
          </Link>
        </p>
      </form>
    </div>
  );
}

export function LoginPage() {
  return <AuthForm mode="login" />;
}

export function RegisterPage() {
  return <AuthForm mode="register" />;
}

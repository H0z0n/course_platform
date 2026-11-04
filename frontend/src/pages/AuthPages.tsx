import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router";
import { toApiError } from "../api/client";
import { api } from "../api/endpoints";
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
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (user) return <Navigate to={target} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await (isLogin ? login(email, password) : register(email, password, consent));
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
          <span className="field-head">
            <span>Пароль</span>
            {isLogin && (
              <Link to="/forgot-password" className="small">
                Забыли пароль?
              </Link>
            )}
          </span>
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
        {!isLogin && (
          <label className="checkbox consent">
            <input
              type="checkbox"
              required
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span className="small">
              Даю <Link to="/legal/consent" target="_blank">согласие на обработку персональных данных</Link>{" "}
              и принимаю <Link to="/legal/privacy" target="_blank">политику конфиденциальности</Link>
            </span>
          </label>
        )}
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

export function ForgotPasswordPage() {
  usePageTitle("Восстановление пароля");
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      setSent((await api.auth.requestPasswordReset(email)).detail);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Восстановление пароля</h1>
        {sent ? (
          <div className="alert alert-success">{sent}. Проверьте почту, в том числе папку «Спам».</div>
        ) : (
          <>
            <p className="muted">Укажите email, с которым регистрировались, — пришлём ссылку для нового пароля.</p>
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
            {error && <ErrorMessage error={error} />}
            <button type="submit" className="btn btn-primary btn-block" disabled={pending}>
              {pending ? "Отправляем…" : "Отправить ссылку"}
            </button>
          </>
        )}
        <p className="muted center">
          <Link to="/login">Вернуться ко входу</Link>
        </p>
      </form>
    </div>
  );
}

export function ResetPasswordPage() {
  usePageTitle("Новый пароль");
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== repeat) {
      setError("Пароли не совпадают");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await api.auth.confirmPasswordReset(token, password);
      setDone(true);
    } catch (reason) {
      setError(toApiError(reason).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Новый пароль</h1>
        {!token && <ErrorMessage error="В ссылке нет кода восстановления. Запросите письмо ещё раз." />}
        {done ? (
          <>
            <div className="alert alert-success">Пароль изменён.</div>
            <Link to="/login" className="btn btn-primary btn-block">
              Войти
            </Link>
          </>
        ) : (
          token && (
            <>
              <label className="field">
                <span>Новый пароль</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <small className="muted">Не короче 8 символов</small>
              </label>
              <label className="field">
                <span>Повторите пароль</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={repeat}
                  onChange={(event) => setRepeat(event.target.value)}
                />
              </label>
              {error && <ErrorMessage error={error} />}
              <button type="submit" className="btn btn-primary btn-block" disabled={pending}>
                {pending ? "Сохраняем…" : "Сохранить пароль"}
              </button>
            </>
          )
        )}
        {!done && (
          <p className="muted center">
            <Link to="/forgot-password">Запросить новую ссылку</Link>
          </p>
        )}
      </form>
    </div>
  );
}

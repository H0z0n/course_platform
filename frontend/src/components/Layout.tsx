import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { isStaff, useAuth } from "../auth/AuthContext";
import { useSite } from "../site/SiteContext";
import { ThemeSwitcher } from "../theme/ThemeSwitcher";

export function Layout() {
  const { user, logout } = useAuth();
  const { site_name } = useSite();
  const navigate = useNavigate();

  return (
    <div className="app">
      <header className="header">
        <div className="container header-inner">
          <Link to="/" className="brand">
            {site_name}
          </Link>
          <nav className="nav" aria-label="Основная навигация">
            <NavLink to="/" end>
              Каталог
            </NavLink>
            {user && <NavLink to="/my">Моё обучение</NavLink>}
            {isStaff(user) && <NavLink to="/admin">Управление</NavLink>}
          </nav>
          <div className="header-user">
            <ThemeSwitcher />
            {user ? (
              <>
                <span className="user-email" title={user.email}>
                  {user.email}
                </span>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                >
                  Выйти
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost btn-sm">
                  Войти
                </Link>
                <Link to="/register" className="btn btn-primary btn-sm">
                  Регистрация
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container">
          © {new Date().getFullYear()} {site_name}
        </div>
      </footer>
    </div>
  );
}

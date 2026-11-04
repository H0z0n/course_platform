import { NavLink, Outlet } from "react-router";
import { useAuth } from "../../auth/AuthContext";

export function AdminLayout() {
  const { user } = useAuth();
  return (
    <div className="container admin">
      <div className="admin-head">
        <h1>Управление</h1>
        <nav className="tabs" aria-label="Разделы управления">
          <NavLink to="/admin" end>
            Курсы
          </NavLink>
          <NavLink to="/admin/purchases">Покупки</NavLink>
          <NavLink to="/admin/users">Пользователи</NavLink>
          {user?.role === "owner" && <NavLink to="/admin/branding">Оформление</NavLink>}
          {user?.role === "owner" && <NavLink to="/admin/documents">Документы</NavLink>}
        </nav>
      </div>
      <Outlet />
    </div>
  );
}

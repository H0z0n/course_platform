import { NavLink, Outlet } from "react-router";

export function AdminLayout() {
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
        </nav>
      </div>
      <Outlet />
    </div>
  );
}

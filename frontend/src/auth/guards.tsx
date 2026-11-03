import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { EmptyState, Spinner } from "../components/ui";
import { isStaff, useAuth } from "./AuthContext";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner />;
  if (user === null) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

export function RequireStaff({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner />;
  if (user === null) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (!isStaff(user)) {
    return (
      <div className="container">
        <EmptyState title="Нет доступа">Этот раздел доступен только администраторам.</EmptyState>
      </div>
    );
  }
  return children;
}

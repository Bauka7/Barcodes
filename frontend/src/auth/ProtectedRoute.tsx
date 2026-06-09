import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./AuthProvider";

export function ProtectedRoute() {
  const { loading, token, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="page-loader">
        <div>Загрузка сессии...</div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

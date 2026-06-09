import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";

import { AuthProvider } from "./auth/AuthProvider";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { I18nProvider } from "./i18n";
import { AppLayout } from "./layout/AppLayout";
import { BatchDetailPage } from "./pages/BatchDetailPage";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { GenerateBarcodePage } from "./pages/GenerateBarcodePage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";
import { PdfPage } from "./pages/PdfPage";
import { PrintHistoryPage } from "./pages/PrintHistoryPage";
import { SearchPage } from "./pages/SearchPage";

const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/app",
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/app/departments" replace /> },
          { path: "departments", element: <DepartmentsPage /> },
          { path: "generate", element: <GenerateBarcodePage /> },
          { path: "history", element: <HistoryPage /> },
          { path: "history/:batchId", element: <BatchDetailPage /> },
          { path: "search", element: <SearchPage /> },
          { path: "pdf", element: <PdfPage /> },
          { path: "pdf/:batchId", element: <PdfPage /> },
          { path: "print-history", element: <PrintHistoryPage /> },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/app/departments" replace />,
  },
]);

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </I18nProvider>
  );
}

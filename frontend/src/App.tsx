import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { useAuth } from './auth/AuthContext';
import type { Role } from './types';
import LoginPage from './pages/LoginPage';
import GeneratePage from './pages/GeneratePage';
import JournalPage from './pages/JournalPage';
import BatchDetailPage from './pages/BatchDetailPage';
import SearchPage from './pages/SearchPage';
import BarcodeDetailPage from './pages/BarcodeDetailPage';
import LifecyclePage from './pages/LifecyclePage';
import PrintPage from './pages/PrintPage';
import DepartmentsPage from './pages/DepartmentsPage';
import RangesPage from './pages/RangesPage';
import RangeRequestsPage from './pages/RangeRequestsPage';
import MyRangesPage from './pages/MyRangesPage';
import CodesPage from './pages/CodesPage';
import ClientsPage from './pages/ClientsPage';
import UsersPage from './pages/UsersPage';
import AuditPage from './pages/AuditPage';
import SettingsPage from './pages/SettingsPage';

const STAFF: Role[] = ['admin', 'operator'];
const ADMIN: Role[] = ['admin'];
const CLIENT: Role[] = ['client'];

// Гейт по роли поверх общего гарда авторизации.
function gated(roles: Role[], el: React.ReactNode) {
  return <ProtectedRoute roles={roles}>{el}</ProtectedRoute>;
}

// Стартовая страница зависит от роли: сотрудник → Генерация, клиент → Мои диапазоны.
function HomeRedirect() {
  const { user } = useAuth();
  const to = user?.role === 'client' ? '/my-ranges' : '/generate';
  return <Navigate to={to} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      {/* всё под каркасом — только для вошедших */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomeRedirect />} />

        {/* все роли */}
        <Route path="/barcodes/:barcode" element={<BarcodeDetailPage />} />
        <Route path="/range-requests" element={<RangeRequestsPage />} />

        {/* client */}
        <Route path="/my-ranges" element={gated(CLIENT, <MyRangesPage />)} />

        {/* admin/operator */}
        <Route path="/generate" element={gated(STAFF, <GeneratePage />)} />
        <Route path="/journal" element={gated(STAFF, <JournalPage />)} />
        <Route path="/journal/:batchId" element={gated(STAFF, <BatchDetailPage />)} />
        <Route path="/search" element={gated(STAFF, <SearchPage />)} />
        <Route path="/lifecycle" element={gated(STAFF, <LifecyclePage />)} />
        <Route path="/print" element={gated(STAFF, <PrintPage />)} />
        <Route path="/departments" element={gated(STAFF, <DepartmentsPage />)} />
        <Route path="/ranges" element={gated(STAFF, <RangesPage />)} />
        <Route path="/codes" element={gated(STAFF, <CodesPage />)} />
        <Route path="/clients" element={gated(STAFF, <ClientsPage />)} />

        {/* admin */}
        <Route path="/users" element={gated(ADMIN, <UsersPage />)} />
        <Route path="/audit" element={gated(ADMIN, <AuditPage />)} />
        <Route path="/settings" element={gated(ADMIN, <SettingsPage />)} />

        <Route path="*" element={<HomeRedirect />} />
      </Route>
    </Routes>
  );
}

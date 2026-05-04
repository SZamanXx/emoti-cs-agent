import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Inbox from "./pages/Inbox";
import TicketPage from "./pages/TicketPage";
import KbPage from "./pages/KbPage";
import SettingsPage from "./pages/SettingsPage";
import MetricsPage from "./pages/MetricsPage";
import NewTicketPage from "./pages/NewTicketPage";
import LoginPage from "./pages/LoginPage";
import { AuthProvider, useAuth } from "./lib/auth";

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Layout />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoutes />}>
          <Route path="/" element={<Navigate to="/inbox" replace />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/inbox/new" element={<NewTicketPage />} />
          <Route path="/ticket/:id" element={<TicketPage />} />
          <Route path="/kb" element={<KbPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

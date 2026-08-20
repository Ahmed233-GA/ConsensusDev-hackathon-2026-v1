import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { NavigationProvider } from "@/context/NavigationContext";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { PullRequestPage } from "@/pages/PullRequestPage";
import { PullRequestsListPage } from "@/pages/PullRequestsListPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AgentsPage } from "@/pages/AgentsPage";
import { PipelinesPage } from "@/pages/PipelinesPage";
import { LogsPage } from "@/pages/LogsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavigationProvider>
          <Routes>
            {/* Public Login Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/pull-requests" element={<PullRequestsListPage />} />
              <Route path="/pull-requests/:id" element={<PullRequestPage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/pipelines" element={<PipelinesPage />} />
              <Route path="/logs" element={<LogsPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </NavigationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

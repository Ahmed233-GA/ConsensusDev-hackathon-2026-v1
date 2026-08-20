import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { NavigationProvider } from "@/context/NavigationContext";
import { PullRequestPage } from "@/pages/PullRequestPage";
import { PullRequestsListPage } from "@/pages/PullRequestsListPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AgentsPage } from "@/pages/AgentsPage";
import { PipelinesPage } from "@/pages/PipelinesPage";
import { LogsPage } from "@/pages/LogsPage";

export default function App() {
  return (
    <BrowserRouter>
      <NavigationProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Navigate to="/pull-requests/pr-1248" replace />} />
            <Route path="/pull-requests" element={<PullRequestsListPage />} />
            <Route path="/pull-requests/:id" element={<PullRequestPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="*" element={<Navigate to="/pull-requests/pr-1248" replace />} />
          </Route>
        </Routes>
      </NavigationProvider>
    </BrowserRouter>
  );
}

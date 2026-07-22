import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Cases from "./pages/Cases.jsx";
import CaseDetail from "./pages/CaseDetail.jsx";
import MapView from "./pages/MapView.jsx";
import NetworkGraph from "./pages/NetworkGraph.jsx";
import AuditTrail from "./pages/AuditTrail.jsx";
import Layout from "./components/Layout.jsx";
import { getCurrentUser } from "./lib/api.js";

function ProtectedRoute({ children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/cases" element={<Cases />} />
                <Route path="/cases/:id" element={<CaseDetail />} />
                <Route path="/map" element={<MapView />} />
                <Route path="/network" element={<NetworkGraph />} />
                <Route path="/audit" element={<AuditTrail />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

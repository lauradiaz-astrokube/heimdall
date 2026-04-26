import { Routes, Route } from "react-router-dom";
import { AuthGuard } from "./auth/AuthGuard";
import { DashboardPage } from "./pages/DashboardPage";
import { CallbackPage } from "./pages/CallbackPage";
import { RequestPage } from "./pages/RequestPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";

// ---------------------------------------------------------------------------
// Rutas del portal JIT
//
// /callback  → Recibe el código OIDC de Identity Center (pública)
// /          → Dashboard principal (protegida)
// /request   → Formulario de solicitud de acceso (protegida)
// /approvals → Panel de aprobaciones (protegida, solo aprobadores)
// ---------------------------------------------------------------------------

export default function App() {
  return (
    <Routes>
      {/* Ruta pública: Identity Center redirige aquí tras el login */}
      <Route path="/callback" element={<CallbackPage />} />

      {/* Rutas protegidas */}
      <Route
        path="/"
        element={
          <AuthGuard>
            <DashboardPage />
          </AuthGuard>
        }
      />
      <Route
        path="/request"
        element={
          <AuthGuard>
            <RequestPage />
          </AuthGuard>
        }
      />
      <Route
        path="/approvals"
        element={
          <AuthGuard>
            <ApprovalsPage />
          </AuthGuard>
        }
      />
    </Routes>
  );
}

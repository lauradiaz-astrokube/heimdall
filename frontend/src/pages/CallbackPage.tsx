import { useEffect } from "react";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router-dom";
import logoClaro from "../modo-claro-logo.png";

export function CallbackPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!auth.isLoading && auth.isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [auth.isLoading, auth.isAuthenticated, navigate]);

  if (auth.error) {
    return (
      <div className="hscreen flex items-center justify-center">
        <div className="hcard p-8 max-w-sm w-full text-center">
          <p className="font-bold text-red-500 mb-1">Error al completar el login</p>
          <p className="text-sm htext-2">{auth.error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="hscreen flex items-center justify-center">
      <div className="flex flex-col items-center gap-5">
        <img src={logoClaro} alt="HeimdALL" className="h-20 w-20 object-contain" />
        <div className="h-[3px] w-40 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
          <div className="h-full w-full animate-pulse rounded-full"
            style={{ background: "linear-gradient(90deg, #1d4ed8, #7c3aed, #c9a84b)" }} />
        </div>
        <p className="text-xs tracking-widest uppercase htext-3">
          Completando autenticación...
        </p>
      </div>
    </div>
  );
}

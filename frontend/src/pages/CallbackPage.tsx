import { useEffect } from "react";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router-dom";

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
      <div className="flex min-h-screen items-center justify-center bg-[#f0f2f7] dark:bg-[#060a14]">
        <div className="rounded-xl border border-gray-200 dark:border-white/5 bg-white dark:bg-[#0e1525] p-8 max-w-sm w-full text-center">
          <p className="font-bold text-red-500 mb-1">Error al completar el login</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{auth.error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f0f2f7] dark:bg-[#060a14]">
      <div className="flex flex-col items-center gap-5">
        <div className="flex h-12 w-12 items-center justify-center rounded-sm rotate-45 border-2 border-[#c9a84b]">
          <span className="-rotate-45 text-xs font-black text-[#c9a84b]">JIT</span>
        </div>
        <div className="h-[3px] w-40 rounded-full overflow-hidden bg-gray-200 dark:bg-white/10">
          <div className="h-full w-full animate-pulse rounded-full"
            style={{ background: "linear-gradient(90deg, #1d4ed8, #7c3aed, #c9a84b)" }} />
        </div>
        <p className="text-xs tracking-widest uppercase text-gray-400 dark:text-gray-600">
          Completando autenticación...
        </p>
      </div>
    </div>
  );
}

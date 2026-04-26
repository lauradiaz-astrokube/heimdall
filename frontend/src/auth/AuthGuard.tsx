import { useAuth } from "react-oidc-context";
import { ReactNode } from "react";
import { useI18n } from "../i18n/I18nContext";
import logoClaro from "../modo-claro-logo.png";

function BifrostLoader({ label }: { label: string }) {
  return (
    <div className="hscreen flex items-center justify-center">
      <div className="flex flex-col items-center gap-5">
        <img src={logoClaro} alt="HeimdALL" className="h-20 w-20 object-contain" />
        <div className="h-[3px] w-40 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
          <div className="h-full w-full animate-pulse rounded-full"
            style={{ background: "linear-gradient(90deg, #1d4ed8, #7c3aed, #c9a84b)" }} />
        </div>
        <p className="text-xs tracking-widest uppercase htext-3">{label}</p>
      </div>
    </div>
  );
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const { tr } = useI18n();

  if (auth.isLoading) return <BifrostLoader label={tr.loadingSession} />;

  if (auth.error) {
    return (
      <div className="hscreen flex items-center justify-center">
        <div className="hcard p-8 max-w-sm w-full text-center">
          <p className="font-bold text-red-500 mb-1">{tr.authError}</p>
          <p className="text-sm htext-2 mb-5">{auth.error.message}</p>
          <button onClick={() => auth.signinRedirect()} className="hbtn-gold w-full">
            {tr.retry}
          </button>
        </div>
      </div>
    );
  }

  if (!auth.isAuthenticated) { auth.signinRedirect(); return null; }

  return <>{children}</>;
}

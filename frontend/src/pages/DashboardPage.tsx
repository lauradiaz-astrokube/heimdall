import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { useI18n } from "../i18n/I18nContext";
import apiClient from "../api/client";

interface Grant {
  id: string; account_id: string; account_name: string;
  permission_set_arn: string; permission_set_name: string;
  expires_at: number; status: string;
}

function useCountdown(expiresAt: number, expiredLabel: string) {
  const [remaining, setRemaining] = useState("");
  useEffect(() => {
    function calc() {
      const diff = expiresAt - Math.floor(Date.now() / 1000);
      if (diff <= 0) return setRemaining(expiredLabel);
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      setRemaining([h > 0 ? `${h}h` : "", m > 0 ? `${m}m` : "", `${s}s`].filter(Boolean).join(" "));
    }
    calc();
    const t = setInterval(calc, 1000);
    return () => clearInterval(t);
  }, [expiresAt, expiredLabel]);
  return remaining;
}

function labelFromArn(arn: string) {
  const parts = arn.split("/");
  return parts[parts.length - 1] ?? arn;
}

function GrantCard({ grant, onRevoked }: { grant: Grant; onRevoked: (id: string) => void }) {
  const { tr } = useI18n();
  const countdown = useCountdown(grant.expires_at, tr.expired);
  const secondsLeft = grant.expires_at - Math.floor(Date.now() / 1000);
  const critical = secondsLeft < 600;
  const pct = Math.max(0, Math.min(100, (secondsLeft / (3600 * 24)) * 100));
  const accountLabel = grant.account_name || grant.account_id;
  const permissionLabel = grant.permission_set_name || labelFromArn(grant.permission_set_arn);
  const [revoking, setRevoking] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  const handleRevoke = async () => {
    if (!confirm) { setConfirm(true); setRevokeError(null); return; }
    setRevoking(true);
    try {
      await apiClient.post(`/grants/${grant.id}/revoke`);
      onRevoked(grant.id);
    } catch (err: unknown) {
      setRevoking(false);
      setConfirm(false);
      if (err && typeof err === "object" && "response" in err) {
        const res = (err as { response?: { data?: { detail?: string } } }).response;
        setRevokeError(res?.data?.detail ?? tr.revokeError);
      } else {
        setRevokeError(tr.revokeError);
      }
    }
  };

  return (
    <div className="hcard overflow-hidden">
      <div className="h-[2px] w-full" style={{ backgroundColor: "var(--border)" }}>
        <div className="h-full transition-all duration-1000" style={{
          width: `${pct}%`,
          background: critical ? "#ef4444" : "linear-gradient(90deg, #4f46e5, #c9a84b)"
        }} />
      </div>
      <div className="p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <span className={`mt-1.5 block h-2 w-2 rounded-full flex-shrink-0 ${critical ? "bg-red-500 animate-pulse" : "bg-emerald-400"}`} />
          <div className="flex-1 min-w-0">
            <p className="font-semibold htext-1 truncate">{accountLabel}</p>
            <p className="text-xs font-mono htext-3 mt-0.5 truncate">{grant.account_id}</p>
            <p className="text-sm htext-2 mt-1 truncate">{permissionLabel}</p>
          </div>
          <div className="flex-shrink-0 text-right">
            <div className="text-base sm:text-lg font-bold tabular-nums leading-none"
              style={{ color: critical ? "#ef4444" : "#c9a84b" }}>
              {countdown}
            </div>
            <p className="text-[9px] uppercase tracking-widest htext-3 mt-1">{tr.remaining}</p>
          </div>
        </div>

        {revokeError && (
          <div className="mt-2 rounded-lg px-3 py-2 text-xs"
            style={{ backgroundColor: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)", color: "#ef4444" }}>
            {revokeError}
          </div>
        )}

        <div className="mt-3 flex justify-end">
          <button
            onClick={handleRevoke}
            disabled={revoking}
            onBlur={() => setConfirm(false)}
            className="rounded-lg px-4 py-1.5 text-xs font-semibold transition-all disabled:opacity-40 w-full sm:w-auto"
            style={confirm
              ? { backgroundColor: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.5)", color: "#ef4444" }
              : { backgroundColor: "var(--bg-deep)", border: "1px solid var(--border)", color: "var(--text-3)" }
            }
          >
            {revoking ? tr.revoking : confirm ? tr.revokeConfirm : tr.revoke}
          </button>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { tr } = useI18n();
  const [grants, setGrants] = useState<Grant[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get("/grants/my").then((r) => setGrants(r.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="mb-8 sm:mb-10 text-center">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-px flex-1" style={{ background: "linear-gradient(to right, transparent, var(--border))" }} />
          <span className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.25em] sm:tracking-[0.3em] htext-3 whitespace-nowrap">
            {tr.jitLabel}
          </span>
          <div className="h-px flex-1" style={{ background: "linear-gradient(to left, transparent, var(--border))" }} />
        </div>
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight htext-1">{tr.heroTitle}</h1>
        <p className="mt-2 text-sm htext-2 max-w-md mx-auto">{tr.heroSub}</p>
      </div>

      <div className="hsection">{tr.actions}</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-10 sm:mb-12">
        <Link to="/request" className="hcard p-5 sm:p-6 group relative overflow-hidden transition-all duration-300"
          onMouseEnter={e => (e.currentTarget.style.borderColor = "#c9a84b")}
          onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}>
          <div className="absolute top-0 right-0 h-20 w-20 sm:h-24 sm:w-24 rounded-bl-full opacity-10 group-hover:opacity-25 transition-opacity"
            style={{ background: "radial-gradient(circle, #c9a84b, transparent)" }} />
          <div className="mb-3 sm:mb-4 flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-lg"
            style={{ border: "1px solid rgba(201,168,75,0.3)", backgroundColor: "rgba(201,168,75,0.1)" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#c9a84b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </div>
          <h2 className="font-bold htext-1 group-hover:text-[#c9a84b] transition-colors text-sm sm:text-base">{tr.requestAccess}</h2>
          <p className="mt-1 text-xs sm:text-sm htext-2">{tr.requestAccessSub}</p>
        </Link>

        <Link to="/approvals" className="hcard p-5 sm:p-6 group relative overflow-hidden transition-all duration-300"
          onMouseEnter={e => (e.currentTarget.style.borderColor = "#10b981")}
          onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}>
          <div className="absolute top-0 right-0 h-20 w-20 sm:h-24 sm:w-24 rounded-bl-full opacity-10 group-hover:opacity-25 transition-opacity"
            style={{ background: "radial-gradient(circle, #10b981, transparent)" }} />
          <div className="mb-3 sm:mb-4 flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-lg"
            style={{ border: "1px solid rgba(16,185,129,0.3)", backgroundColor: "rgba(16,185,129,0.1)" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h2 className="font-bold htext-1 group-hover:text-emerald-500 transition-colors text-sm sm:text-base">{tr.pendingApprovals}</h2>
          <p className="mt-1 text-xs sm:text-sm htext-2">{tr.pendingApprovalsSub}</p>
        </Link>
      </div>

      <div className="flex items-center gap-3 mb-4">
        <span className="hsection mb-0">{tr.activeAccesses}</span>
        <div className="h-px flex-1" style={{ backgroundColor: "var(--border)" }} />
        {grants.length > 0 && (
          <span className="rounded-full px-2 py-0.5 text-[10px] font-bold text-[#c9a84b]"
            style={{ border: "1px solid rgba(201,168,75,0.4)", backgroundColor: "rgba(201,168,75,0.1)" }}>
            {grants.length}
          </span>
        )}
      </div>

      {loading ? (
        <div className="hcard p-10 text-center">
          <div className="mx-auto h-[3px] w-32 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
            <div className="h-full w-full animate-pulse rounded-full" style={{ background: "linear-gradient(90deg, #4f46e5, #c9a84b)" }} />
          </div>
          <p className="mt-4 text-sm htext-3">{tr.loading}</p>
        </div>
      ) : grants.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 sm:p-10 text-center" style={{ borderColor: "var(--border)" }}>
          <p className="text-sm htext-3">{tr.noActiveAccesses}</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {grants.map((g) => (
            <GrantCard key={g.id} grant={g} onRevoked={(id) => setGrants(gs => gs.filter(x => x.id !== id))} />
          ))}
        </div>
      )}
    </Layout>
  );
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Layout } from "../components/Layout";
import { useI18n } from "../i18n/I18nContext";
import { getPermissionSets, getAccounts } from "../api/catalog";
import { createRequest } from "../api/requests";

export function RequestPage() {
  const navigate = useNavigate();
  const { tr } = useI18n();
  const [accountId, setAccountId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [permissionSetArn, setPermissionSetArn] = useState("");
  const [permissionSetName, setPermissionSetName] = useState("");
  const [justification, setJustification] = useState("");
  const [durationHours, setDurationHours] = useState(1);
  const [error, setError] = useState("");

  const { data: permissionSets, isLoading: loadingPS } = useQuery({ queryKey: ["permission-sets"], queryFn: getPermissionSets });
  const { data: accounts, isLoading: loadingAccounts } = useQuery({ queryKey: ["accounts"], queryFn: getAccounts });

  const mutation = useMutation({
    mutationFn: createRequest,
    onSuccess: () => navigate("/"),
    onError: () => setError(tr.requestError),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); setError("");
    if (!accountId || !permissionSetArn || justification.length < 10) {
      setError(tr.validationError); return;
    }
    mutation.mutate({ account_id: accountId, account_name: accountName, permission_set_arn: permissionSetArn, permission_set_name: permissionSetName, justification, duration_hours: durationHours });
  };

  const durationLabel = durationHours === 1 ? tr.duration1h : durationHours < 24 ? tr.durationNh(durationHours) : tr.durationMax;

  return (
    <Layout back title={tr.requestAccess}>
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-black tracking-tight htext-1">{tr.requestTitle}</h1>
          <p className="mt-1.5 text-sm htext-2">{tr.requestSub}</p>
        </div>

        {(loadingPS || loadingAccounts) ? (
          <div className="hcard p-10 sm:p-12 text-center">
            <div className="mx-auto h-[3px] w-32 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
              <div className="h-full w-full animate-pulse" style={{ background: "linear-gradient(90deg, #4f46e5, #c9a84b)" }} />
            </div>
            <p className="mt-4 text-sm htext-3">{tr.loadingCatalog}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="hcard p-4 sm:p-6 flex flex-col gap-5 sm:gap-6">

            <div>
              <label className="hlabel">{tr.awsAccount}</label>
              <select className="hselect" value={accountId} onChange={(e) => {
                const acc = accounts?.find((a) => a.id === e.target.value);
                setAccountId(e.target.value); setAccountName(acc?.name ?? "");
              }} required>
                <option value="">{tr.selectAccount}</option>
                {accounts?.map((a) => <option key={a.id} value={a.id}>{a.name} — {a.id}</option>)}
              </select>
            </div>

            <div>
              <label className="hlabel">{tr.accessLevel}</label>
              <select className="hselect" value={permissionSetArn} onChange={(e) => {
                const ps = permissionSets?.find((p) => p.arn === e.target.value);
                setPermissionSetArn(e.target.value); setPermissionSetName(ps?.name ?? "");
              }} required>
                <option value="">{tr.selectPermissionSet}</option>
                {permissionSets?.map((ps) => <option key={ps.arn} value={ps.arn}>{ps.name}{ps.description ? ` — ${ps.description}` : ""}</option>)}
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="hlabel mb-0">{tr.duration}</label>
                <span className="text-sm font-bold" style={{ color: "#c9a84b" }}>{durationLabel}</span>
              </div>
              <input type="range" min={1} max={24} value={durationHours}
                onChange={(e) => setDurationHours(Number(e.target.value))}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                style={{ accentColor: "#c9a84b", backgroundColor: "var(--border)" }} />
              <div className="flex justify-between text-xs htext-3 mt-1.5">
                <span>1h</span><span>24h</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="hlabel mb-0">{tr.justification}</label>
                <span className={`text-xs font-mono ${justification.length >= 10 ? "text-emerald-500" : "htext-3"}`}>
                  {justification.length} / 10 {tr.justificationMin}
                </span>
              </div>
              <textarea className="hinput resize-none" rows={4}
                placeholder={tr.justificationPlaceholder}
                value={justification} onChange={(e) => setJustification(e.target.value)} required minLength={10} />
            </div>

            {error && (
              <div className="rounded-lg border px-4 py-3 text-sm text-red-500"
                style={{ borderColor: "rgba(239,68,68,0.3)", backgroundColor: "rgba(239,68,68,0.08)" }}>
                {error}
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 pt-1">
              <button type="button" onClick={() => navigate("/")} className="hbtn-ghost sm:flex-1 order-2 sm:order-1">
                {tr.cancel}
              </button>
              <button type="submit" disabled={mutation.isPending} className="hbtn-gold sm:flex-1 order-1 sm:order-2">
                {mutation.isPending ? tr.sending : tr.send}
              </button>
            </div>
          </form>
        )}
      </div>
    </Layout>
  );
}

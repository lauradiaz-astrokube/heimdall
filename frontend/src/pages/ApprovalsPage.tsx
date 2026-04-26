import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Layout } from "../components/Layout";
import { useI18n } from "../i18n/I18nContext";
import apiClient from "../api/client";
import { AccessRequest } from "../api/requests";

function extractError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response;
    if (res?.data?.detail) return res.data.detail;
  }
  return "Error inesperado.";
}

const getPendingRequests = (): Promise<AccessRequest[]> =>
  apiClient.get("/requests/pending").then((r) => r.data);
const approveRequest = ({ id, comment }: { id: string; comment: string }) =>
  apiClient.post(`/requests/${id}/approve`, { comment }).then((r) => r.data);
const rejectRequest = ({ id, comment }: { id: string; comment: string }) =>
  apiClient.post(`/requests/${id}/reject`, { comment }).then((r) => r.data);

function RequestCard({ request }: { request: AccessRequest }) {
  const { tr } = useI18n();
  const queryClient = useQueryClient();
  const [comment, setComment] = useState("");
  const [done, setDone] = useState(false);
  const [result, setResult] = useState<"approved" | "rejected" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const approveMutation = useMutation({
    mutationFn: approveRequest,
    onSuccess: () => { setError(null); setDone(true); setResult("approved"); queryClient.invalidateQueries({ queryKey: ["pending-requests"] }); },
    onError: (err) => setError(extractError(err)),
  });
  const rejectMutation = useMutation({
    mutationFn: rejectRequest,
    onSuccess: () => { setError(null); setDone(true); setResult("rejected"); queryClient.invalidateQueries({ queryKey: ["pending-requests"] }); },
    onError: (err) => setError(extractError(err)),
  });

  const isPending = approveMutation.isPending || rejectMutation.isPending;

  if (done) {
    return (
      <div className="hcard p-4 sm:p-5" style={{ borderLeftWidth: "3px", borderLeftColor: result === "approved" ? "#10b981" : "#ef4444" }}>
        <p className="text-sm font-semibold htext-1">{result === "approved" ? tr.accessGranted : tr.requestRejected}</p>
        <p className="text-xs htext-3 mt-0.5 truncate">{request.requestor_email} — {request.permission_set_name}</p>
      </div>
    );
  }

  return (
    <div className="hcard overflow-hidden">
      <div className="h-[2px]" style={{ background: "linear-gradient(90deg, #4f46e5, #c9a84b)" }} />
      <div className="p-4 sm:p-5 flex flex-col gap-4">
        <div>
          <p className="font-semibold htext-1 truncate">{request.requestor_email}</p>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1">
            <span className="text-sm htext-2">{request.permission_set_name}</span>
            <span className="htext-3">·</span>
            <span className="text-sm htext-2">{request.account_name}</span>
            <span className="htext-3">·</span>
            <span className="text-sm font-semibold" style={{ color: "#c9a84b" }}>{request.duration_hours}h</span>
          </div>
          <p className="text-xs font-mono htext-3 mt-1">{new Date(request.created_at).toLocaleString()}</p>
        </div>

        <div className="rounded-lg px-4 py-3" style={{ backgroundColor: "var(--bg-deep)", border: "1px solid var(--border)" }}>
          <p className="text-[10px] font-bold uppercase tracking-widest htext-3 mb-1.5">{tr.justificationLabel}</p>
          <p className="text-sm htext-1">{request.justification}</p>
        </div>

        <input type="text" placeholder={tr.commentPlaceholder} className="hinput"
          value={comment} onChange={(e) => setComment(e.target.value)} disabled={isPending} />

        {error && (
          <div className="rounded-lg px-4 py-3 text-sm text-red-500"
            style={{ backgroundColor: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)" }}>
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <button onClick={() => { setError(null); approveMutation.mutate({ id: request.id, comment }); }} disabled={isPending} className="hbtn-success flex-1">
            {approveMutation.isPending ? tr.approving : tr.approve}
          </button>
          <button onClick={() => { setError(null); rejectMutation.mutate({ id: request.id, comment }); }} disabled={isPending} className="hbtn-danger flex-1">
            {rejectMutation.isPending ? tr.rejecting : tr.reject}
          </button>
        </div>
      </div>
    </div>
  );
}

export function ApprovalsPage() {
  const { tr } = useI18n();
  const { data: requests, isLoading } = useQuery({
    queryKey: ["pending-requests"], queryFn: getPendingRequests, refetchInterval: 30000,
  });

  return (
    <Layout back title={tr.pendingApprovals}>
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-6 sm:mb-7">
          <h1 className="text-xl sm:text-2xl font-black tracking-tight htext-1">{tr.pendingTitle}</h1>
          <p className="mt-1.5 text-sm htext-2">{tr.pendingSub}</p>
        </div>
        <div className="flex flex-col gap-3 sm:gap-4">
          {isLoading && (
            <div className="hcard p-10 text-center">
              <div className="mx-auto h-[3px] w-32 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
                <div className="h-full w-full animate-pulse" style={{ background: "linear-gradient(90deg, #4f46e5, #c9a84b)" }} />
              </div>
              <p className="mt-4 text-sm htext-3">{tr.loading}</p>
            </div>
          )}
          {!isLoading && (!requests || requests.length === 0) && (
            <div className="rounded-xl border border-dashed p-10 text-center" style={{ borderColor: "var(--border)" }}>
              <p className="text-sm htext-3">{tr.noPending}</p>
            </div>
          )}
          {requests?.map((r) => <RequestCard key={r.id} request={r} />)}
        </div>
      </div>
    </Layout>
  );
}

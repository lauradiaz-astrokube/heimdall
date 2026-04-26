import apiClient from "./client";

export interface CreateRequestPayload {
  account_id: string;
  account_name: string;
  permission_set_arn: string;
  permission_set_name: string;
  justification: string;
  duration_hours: number;
}

export interface AccessRequest {
  id: string;
  requestor_email: string;
  account_name: string;
  permission_set_name: string;
  justification: string;
  duration_hours: number;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  created_at: string;
}

export const createRequest = (payload: CreateRequestPayload): Promise<AccessRequest> =>
  apiClient.post("/requests/", payload).then((r) => r.data);

export const getMyRequests = (): Promise<AccessRequest[]> =>
  apiClient.get("/requests/my").then((r) => r.data);

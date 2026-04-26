import apiClient from "./client";

export interface PermissionSet {
  arn: string;
  name: string;
  description: string;
  session_duration: string;
}

export interface Account {
  id: string;
  name: string;
  email: string;
}

export const getPermissionSets = (): Promise<PermissionSet[]> =>
  apiClient.get("/catalog/permission-sets").then((r) => r.data);

export const getAccounts = (): Promise<Account[]> =>
  apiClient.get("/catalog/accounts").then((r) => r.data);

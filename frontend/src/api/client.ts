import axios from "axios";
import { User } from "oidc-client-ts";
import { oidcConfig } from "../auth/authConfig";

// ---------------------------------------------------------------------------
// Cliente HTTP para llamar al backend de HeimdALL.
// Adjunta automáticamente el token JWT de Entra ID en cada petición.
// ---------------------------------------------------------------------------

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

// Interceptor: añade el Bearer token de Entra ID en cada request.
// Usamos el id_token porque su audience es el client_id de la app,
// que es exactamente lo que valida el backend FastAPI.
apiClient.interceptors.request.use((config) => {
  const oidcStorage = sessionStorage.getItem(
    `oidc.user:${oidcConfig.authority}:${oidcConfig.client_id}`
  );

  if (oidcStorage) {
    const user: User = JSON.parse(oidcStorage);
    const token = user?.id_token ?? user?.access_token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

export default apiClient;

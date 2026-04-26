import { WebStorageStateStore } from "oidc-client-ts";

// ---------------------------------------------------------------------------
// Configuración OIDC para Microsoft Entra ID
//
// Entra ID es el proveedor de identidades real. Identity Center confía en
// los tokens que emite Entra ID via el trusted token issuer configurado.
//
// Valores obtenidos de: Entra ID → App registrations → HeimdALL
// ---------------------------------------------------------------------------

const ENTRA_TENANT_ID = import.meta.env.VITE_ENTRA_TENANT_ID;
// Ejemplo: "3b0c8f43-8bb8-4fa1-b05c-e0e3283adad6"

const CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID;
// Ejemplo: "00772941-efea-46a9-903e-338c46852d3e"

const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI ?? `${window.location.origin}/callback`;

export const oidcConfig = {
  // Entra ID como authority — él es quien autentica al usuario
  authority: `https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0`,

  client_id: CLIENT_ID,
  redirect_uri: REDIRECT_URI,

  // PKCE obligatorio para SPAs (sin client_secret)
  response_type: "code",

  // openid + profile + email básicos
  // groups permite que el backend sepa a qué grupos pertenece el usuario
  scope: "openid profile email",

  // sessionStorage es más seguro que localStorage para tokens
  userStore: new WebStorageStateStore({ store: window.sessionStorage }),

  post_logout_redirect_uri: window.location.origin,

  // Renovación silenciosa del token antes de que caduque
  automaticSilentRenew: true,
  silent_redirect_uri: `${window.location.origin}/silent-renew`,
};

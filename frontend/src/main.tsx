import React from "react";
import ReactDOM from "react-dom/client";
import { AuthProvider } from "react-oidc-context";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { oidcConfig } from "./auth/authConfig";
import { ThemeProvider } from "./theme/ThemeContext";
import "./index.css";

const queryClient = new QueryClient();

// Callback que se ejecuta cuando el login con Identity Center completa.
// Limpia los parámetros OIDC de la URL y redirige a la ruta original.
const onSigninCallback = () => {
  window.history.replaceState({}, document.title, window.location.pathname);
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider {...oidcConfig} onSigninCallback={onSigninCallback}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter basename={import.meta.env.BASE_URL}>
            <App />
          </BrowserRouter>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);

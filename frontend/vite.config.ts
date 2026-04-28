import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // VITE_BASE_URL=/heimdall/ para GitHub Pages, / para Kubernetes
  base: process.env.VITE_BASE_URL ?? "/",
});

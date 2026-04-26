import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Base necesario para GitHub Pages (sirve desde /heimdall/)
  base: process.env.NODE_ENV === "production" ? "/heimdall/" : "/",
});

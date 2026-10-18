
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Production build is served by FastAPI on the same origin (no CDN).
// Dev server proxies /api to the local backend so the browser never calls a
// different host directly.
export default defineConfig({
  root: "frontend",
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: false,
      },
    },
  },
});

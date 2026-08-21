import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/predict": "http://127.0.0.1:8000",
      "/ask": "http://127.0.0.1:8000",
      "/extract": "http://127.0.0.1:8000",
      "/classify": "http://127.0.0.1:8000",
      "/metrics": "http://127.0.0.1:8000",
      "/token": "http://127.0.0.1:8000",
      "/history": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000",
    },
  },
});

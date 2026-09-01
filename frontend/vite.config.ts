import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 2671,
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:5039",
        changeOrigin: true,
      },
      "/ws": {
        target: process.env.VITE_WS_BACKEND_URL || "ws://localhost:5039",
        ws: true,
      },
    },
  },
});

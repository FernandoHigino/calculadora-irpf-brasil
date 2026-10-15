import { fileURLToPath } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const projectRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    fs: {
      allow: [projectRoot],
    },
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});

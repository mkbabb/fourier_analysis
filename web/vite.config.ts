import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import latexPaperPlugin from "./plugins/vite-plugin-latex-paper";

export default defineConfig({
    plugins: [latexPaperPlugin(), vue()],
    base: process.env.VITE_BASE_URL || "/",
    resolve: {
        alias: {
            "@": fileURLToPath(new URL("./src", import.meta.url)),
        },
    },
    css: {
        postcss: {
            plugins: [(await import("@tailwindcss/postcss")).default],
        },
    },
    appType: "spa",
    server: {
        port: 3000,
        proxy: {
            "/api": {
                target: process.env.VITE_PROXY_API || "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
});

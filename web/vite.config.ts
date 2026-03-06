import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
    plugins: [vue()],
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
                target: process.env.VITE_API_URL || "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
});

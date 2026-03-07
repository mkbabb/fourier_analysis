import { createRouter, createWebHistory } from "vue-router";
import PaperView from "@/components/paper/PaperView.vue";
import VisualizationView from "@/components/visualization/VisualizationView.vue";

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/",
            redirect: () => {
                const saved = localStorage.getItem("fourier_active_tab");
                return saved === "/visualize" ? "/visualize" : "/paper";
            },
        },
        {
            path: "/paper",
            name: "paper",
            component: PaperView,
        },
        {
            path: "/visualize",
            name: "visualize",
            component: VisualizationView,
            beforeEnter: (_to, _from, next) => {
                // If a session slug is stored, redirect to /s/:slug
                const slug = localStorage.getItem("fourier_last_slug");
                if (slug) {
                    next(`/s/${slug}`);
                } else {
                    next();
                }
            },
        },
        {
            path: "/s/:slug",
            name: "session",
            component: VisualizationView,
            props: true,
        },
    ],
});

// Persist active tab on navigation
router.afterEach((to) => {
    if (to.path === "/paper" || to.path === "/visualize") {
        localStorage.setItem("fourier_active_tab", to.path);
    } else if (to.path.startsWith("/s/")) {
        localStorage.setItem("fourier_active_tab", "/visualize");
        // Extract and save the slug for tab-switching
        const slug = to.params.slug as string;
        if (slug) localStorage.setItem("fourier_last_slug", slug);
    }
});

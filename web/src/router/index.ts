import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/",
            redirect: "/paper",
        },
        {
            path: "/paper",
            name: "paper",
            component: () => import("@/components/paper/PaperView.vue"),
        },
        {
            path: "/visualize",
            name: "visualize",
            component: () => import("@/components/visualization/VisualizationView.vue"),
        },
        {
            path: "/s/:slug",
            name: "session",
            component: () => import("@/components/visualization/VisualizationView.vue"),
            props: true,
        },
    ],
});

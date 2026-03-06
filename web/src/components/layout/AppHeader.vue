<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "@/stores/session";
import { Copy, Check, FileText, Sparkles } from "lucide-vue-next";
import DarkModeToggle from "./DarkModeToggle.vue";

const route = useRoute();
const store = useSessionStore();

const copied = ref(false);

const tabs = [
    { name: "Paper", path: "/paper", icon: FileText },
    { name: "Visualize", path: "/visualize", icon: Sparkles },
] as const;

function isActive(path: string) {
    return route.path === path || (path === "/visualize" && route.path.startsWith("/s/"));
}

async function copySlug() {
    if (!store.slug) return;
    const url = `${window.location.origin}/s/${store.slug}`;
    await navigator.clipboard.writeText(url);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
}
</script>

<template>
    <header
        class="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    >
        <div class="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6">
            <!-- Logo / Title -->
            <router-link to="/" class="flex items-center gap-2.5 group">
                <div
                    class="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground transition-transform duration-300 group-hover:scale-105"
                >
                    <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M2 12c2-4 4-8 6-8s4 8 6 8 4-8 6-8 2 4 2 8" />
                    </svg>
                </div>
                <span class="fraunces text-lg font-semibold tracking-tight">
                    Fourier Analysis
                </span>
            </router-link>

            <!-- Nav tabs -->
            <nav class="ml-4 flex items-center gap-1">
                <router-link
                    v-for="tab in tabs"
                    :key="tab.path"
                    :to="tab.path"
                    class="relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-200 btn-press"
                    :class="{
                        'bg-muted text-foreground shadow-sm': isActive(tab.path),
                        'text-muted-foreground hover:text-foreground hover:bg-muted/50': !isActive(tab.path),
                    }"
                >
                    <component :is="tab.icon" class="h-3.5 w-3.5" />
                    {{ tab.name }}
                </router-link>
            </nav>

            <div class="flex-1" />

            <!-- Session slug with copy -->
            <Transition name="fade">
                <div
                    v-if="store.slug"
                    class="flex items-center gap-1.5"
                >
                    <span class="fira-code text-xs text-muted-foreground">
                        {{ store.slug }}
                    </span>
                    <button
                        class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-all duration-200 hover:bg-muted hover:text-foreground btn-press"
                        title="Copy session URL"
                        @click="copySlug"
                    >
                        <Transition name="icon-swap" mode="out-in">
                            <Check v-if="copied" class="h-3.5 w-3.5 text-green-500" />
                            <Copy v-else class="h-3.5 w-3.5" />
                        </Transition>
                    </button>
                </div>
            </Transition>

            <!-- Dark mode toggle -->
            <DarkModeToggle />
        </div>
    </header>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
.icon-swap-enter-active,
.icon-swap-leave-active {
    transition: all 0.15s ease;
}
.icon-swap-enter-from {
    opacity: 0;
    transform: scale(0.8);
}
.icon-swap-leave-to {
    opacity: 0;
    transform: scale(0.8);
}
</style>

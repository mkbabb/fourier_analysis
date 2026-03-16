<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useHoverCard } from "./composables/useHoverCard";
import { useWorkspaceStore } from "@/stores/workspace";
import { useGalleryStore } from "@/stores/gallery";
import DarkModeToggle from "./DarkModeToggle.vue";
import UserSlugBar from "@/components/visualization/gallery/UserSlugBar.vue";
import { Shield, ChevronDown, FileText, Eye, LayoutGrid, Sigma, Shuffle } from "lucide-vue-next";
import {
    DropdownMenuRoot,
    DropdownMenuTrigger,
    DropdownMenuPortal,
    DropdownMenuContent,
    DropdownMenuItem,
} from "reka-ui";

const route = useRoute();
const router = useRouter();

const { isOpen: cardOpen, toggle: toggleCard, close: closeCard, onHoverEnter, onHoverLeave } = useHoverCard();

// Close hover card on outside click (for touch devices)
function onDocClick() { closeCard(); }
onMounted(() => document.addEventListener("click", onDocClick));
onUnmounted(() => document.removeEventListener("click", onDocClick));

const tabs = [
    { label: "Paper", value: "/paper", icon: FileText },
    { label: "Visualize", value: "/visualize", icon: Eye },
    { label: "Gallery", value: "/gallery", icon: LayoutGrid },
    { label: "Equation", value: "/equation", icon: Sigma },
    { label: "Morph", value: "/morph", icon: Shuffle },
];

const activeTab = computed(() => {
    if (route.path === "/paper") return "/paper";
    if (route.path === "/visualize" || route.path.startsWith("/s/") || route.path.startsWith("/w/")) return "/visualize";
    if (route.path === "/equation") return "/equation";
    if (route.path === "/gallery") return "/gallery";
    if (route.path === "/morph") return "/morph";
    return "/paper";
});

const activeTabData = computed(() => tabs.find((t) => t.value === activeTab.value) ?? tabs[0]);

function onTabSelect(path: string) {
    router.push(path);
}

const workspaceStore = useWorkspaceStore();
const galleryStore = useGalleryStore();
</script>

<template>
    <header class="app-header sticky top-0 z-50 bg-background/90 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div class="header-inner">
            <!-- Logo with attribution hover card -->
            <div
                class="logo-trigger relative shrink-0"
                role="button"
                tabindex="0"
                aria-label="Go to paper"
                @click.stop="router.push('/paper')"
                @keydown.enter="router.push('/paper')"
                @mouseenter="onHoverEnter"
                @mouseleave="onHoverLeave"
            >
                <span class="logo-mark cm-serif font-semibold tracking-tight cursor-pointer select-none">
                    <span class="fourier-f">&#x2131;</span><span class="logo-text">ourier analysis</span>
                </span>

                <!-- Hover card -->
                <div class="hover-card" :class="{ 'is-open': cardOpen }">
                    <div class="flex items-center gap-3">
                        <img
                            src="https://avatars.githubusercontent.com/u/2848617?v=4"
                            alt="mkbabb"
                            class="h-10 w-10 rounded-full shrink-0"
                        />
                        <div class="flex-1 min-w-0">
                            <a
                                href="https://github.com/mkbabb"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="fira-code text-sm font-normal text-foreground hover:underline"
                                @click.stop
                            >@mbabb</a>
                            <p class="mt-0.5 text-xs italic text-muted-foreground">Fourier analysis &amp; orthogonal decomposition</p>
                        </div>
                    </div>
                    <hr class="my-2 border-border/50" />
                    <a
                        href="https://github.com/mkbabb/fourier-analysis"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="block text-sm text-foreground hover:underline"
                        @click.stop
                    >View project on GitHub 🎉</a>
                </div>
            </div>

            <div class="header-divider" />

            <DropdownMenuRoot>
                <DropdownMenuTrigger as-child>
                    <button class="nav-trigger">
                        <component :is="activeTabData.icon" class="nav-trigger-icon" />
                        <span class="nav-trigger-label">{{ activeTabData.label }}</span>
                        <ChevronDown class="nav-trigger-chevron" />
                    </button>
                </DropdownMenuTrigger>
                <DropdownMenuPortal>
                    <DropdownMenuContent class="nav-dropdown" :side-offset="6" align="start">
                        <DropdownMenuItem
                            v-for="tab in tabs"
                            :key="tab.value"
                            class="nav-dropdown-item"
                            :class="{ 'is-active': activeTab === tab.value }"
                            @select="onTabSelect(tab.value)"
                        >
                            <component :is="tab.icon" class="nav-item-icon" />
                            <span>{{ tab.label }}</span>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenuPortal>
            </DropdownMenuRoot>

            <div class="ml-auto flex items-center gap-1.5 shrink-0">
                <div v-if="galleryStore.adminMode" class="admin-badge" title="Admin mode active">
                    <Shield :size="14" />
                </div>
                <UserSlugBar />
                <DarkModeToggle class="dark-mode-toggle" />
            </div>
        </div>
    </header>
</template>

<style scoped>
@reference "tailwindcss";
.app-header {
    font-feature-settings: "liga", "kern";
}

.header-inner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.5rem;
}

@media (min-width: 640px) {
    .header-inner {
        height: 3.5rem;
        gap: 1rem;
        padding: 0 1.5rem;
    }
}

/* ── Nav trigger (dropdown button) ── */
.nav-trigger {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.3125rem 0.625rem;
    border-radius: 0.4375rem;
    border: none;
    background: hsl(var(--muted) / 0.5);
    color: hsl(var(--foreground));
    font-family: "CMU Serif", "Computer Modern", Georgia, serif;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s ease, box-shadow 0.15s ease;
    white-space: nowrap;
    -webkit-tap-highlight-color: transparent;
}

.nav-trigger:hover {
    background: hsl(var(--muted) / 0.8);
}

.nav-trigger:focus-visible {
    outline: 2px solid hsl(var(--ring));
    outline-offset: 2px;
}

.nav-trigger-icon {
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
    color: var(--viz-amber);
    filter: drop-shadow(0 0 3px color-mix(in srgb, var(--viz-amber) 40%, transparent));
}

.nav-trigger-label {
    display: none;
    color: var(--viz-amber);
}

.nav-trigger-chevron {
    width: 0.875rem;
    height: 0.875rem;
    opacity: 0.5;
    flex-shrink: 0;
    transition: transform 0.2s ease;
}

.nav-trigger[data-state="open"] .nav-trigger-chevron {
    transform: rotate(180deg);
}

@media (min-width: 640px) {
    .nav-trigger {
        padding: 0.375rem 0.75rem;
        font-size: 0.875rem;
    }
    .nav-trigger-label {
        display: inline;
    }
}

/* Mobile: compact logo, divider, toggle sizing */
.logo-mark {
    @apply text-lg;
}

.logo-text {
    display: none;
}

.header-divider {
    width: 1px;
    height: 1rem;
    background: hsl(var(--foreground) / 0.15);
    flex-shrink: 0;
}

.dark-mode-toggle {
    --toggle-size: 2.25rem;
}

@media (min-width: 640px) {
    .logo-mark {
        @apply text-xl;
    }
    .logo-text {
        display: inline;
    }
    .header-divider {
        height: 1.25rem;
    }
    .dark-mode-toggle {
        --toggle-size: 2.75rem;
    }
}

/* ── Admin badge ── */
.admin-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 9999px;
    background: hsl(45, 100%, 50%, 0.1);
    color: hsl(45, 100%, 50%);
    flex-shrink: 0;
}

/* ── Attribution hover card ── */
.logo-trigger {
    cursor: pointer;
}

.hover-card {
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 0.25rem;
    padding: 0.875rem 1rem;
    background: color-mix(in srgb, hsl(var(--popover)) 85%, transparent);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    border: 1.5px solid hsl(var(--border) / 0.4);
    border-radius: 0.75rem;
    opacity: 0;
    pointer-events: none;
    transform: scale(0.92) translateY(6px);
    transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 60;
    min-width: 17rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* Bridge gap so hover doesn't drop */
.hover-card::before {
    content: '';
    position: absolute;
    top: -0.75rem;
    left: 0;
    right: 0;
    height: 0.75rem;
}

.hover-card.is-open {
    opacity: 1;
    pointer-events: auto;
    transform: scale(1) translateY(0);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}

/* Share button enter/leave */
.share-pop-enter-active {
    transition: opacity 0.25s ease, transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.share-pop-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}
.share-pop-enter-from {
    opacity: 0;
    transform: scale(0.5);
}
.share-pop-leave-to {
    opacity: 0;
    transform: scale(0.5);
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>

<!-- Global style for portaled dropdown -->
<style>
.nav-dropdown {
    z-index: 100;
    min-width: 12rem;
    padding: 0.5rem;
    background: color-mix(in srgb, hsl(var(--popover)) 85%, transparent);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1.5px solid hsl(var(--border) / 0.4);
    border-radius: 0.75rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    animation: nav-dropdown-in 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes nav-dropdown-in {
    from {
        opacity: 0;
        transform: scale(0.95) translateY(-4px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

.nav-dropdown-item {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: none;
    background: none;
    color: hsl(var(--foreground) / 0.6);
    font-family: "CMU Serif", "Computer Modern", Georgia, serif;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    outline: none;
}

.nav-dropdown-item:hover,
.nav-dropdown-item[data-highlighted] {
    background: hsl(var(--foreground) / 0.06);
    color: hsl(var(--foreground));
}

.nav-dropdown-item.is-active {
    color: var(--viz-amber);
    background: color-mix(in srgb, var(--viz-amber) 8%, transparent);
}

.nav-dropdown-item.is-active .nav-item-icon {
    filter: drop-shadow(0 0 3px color-mix(in srgb, var(--viz-amber) 50%, transparent));
}

.nav-item-icon {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
}
</style>

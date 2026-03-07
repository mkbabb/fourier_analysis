<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useHoverCard } from "@/composables/useHoverCard";
import DarkModeToggle from "./DarkModeToggle.vue";
import BouncyToggle from "@/components/ui/BouncyToggle.vue";

const route = useRoute();
const router = useRouter();

const { isOpen: cardOpen, toggle: toggleCard, onHoverEnter, onHoverLeave } = useHoverCard();

const tabOptions = [
    { label: "Paper", value: "/paper" },
    { label: "Visualize", value: "/visualize" },
];

const activeTab = computed(() => {
    if (route.path === "/paper") return "/paper";
    if (route.path === "/visualize" || route.path.startsWith("/s/")) return "/visualize";
    return "/paper";
});

function onTabChange(path: string) {
    router.push(path);
}
</script>

<template>
    <header class="app-header sticky top-0 z-50 bg-background/90 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div class="flex h-14 items-center gap-4 px-4 sm:px-6">
            <!-- Logo with attribution hover card -->
            <div
                class="logo-trigger relative"
                role="button"
                tabindex="0"
                aria-label="Show project info"
                @click.stop="toggleCard"
                @keydown.enter="toggleCard"
                @mouseenter="onHoverEnter"
                @mouseleave="onHoverLeave"
            >
                <span class="cm-serif text-lg font-semibold tracking-tight cursor-pointer select-none">
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
                                class="fira-code text-sm font-semibold text-foreground hover:underline"
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

            <div class="h-5 w-px bg-foreground/15" />

            <BouncyToggle
                :options="tabOptions"
                :model-value="activeTab"
                @update:model-value="onTabChange"
            />

            <div class="ml-auto flex items-center gap-1.5">
                <DarkModeToggle style="--toggle-size: 2.75rem" />
            </div>
        </div>
    </header>
</template>

<style scoped>
.app-header {
    font-feature-settings: "liga", "kern";
}

.fourier-f {
    font-size: 1.35em;
    line-height: 1;
    vertical-align: -0.05em;
    font-weight: 700;
}

/* Mobile: hide "ourier analysis" text */
.logo-text {
    display: none;
}
@media (min-width: 640px) {
    .logo-text {
        display: inline;
    }
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

</style>

<script setup lang="ts">
import {
    PaperSectionContent,
    usePaperReader,
    useKatex,
    PAPER_CONTEXT,
    type PaperContext,
} from "@mkbabb/latex-paper/vue";
import "@mkbabb/latex-paper/theme";
import PaperSidebar from "./PaperSidebar.vue";
import MobileFloatingToc from "./MobileFloatingToc.vue";
import { paperSections, labelMap } from "@/lib/paperContent";
import type { PaperSectionData } from "@/lib/paperContent";
import { ref, computed, provide, onMounted, onUnmounted, nextTick } from "vue";
import { ArrowRight } from "lucide-vue-next";

// ── KaTeX with app-specific macros ─────────────────────────
const macros: Record<string, string> = {
    "\\deriv": "\\mathrm{d}",
    "\\ihat": "\\boldsymbol{\\hat{\\imath}}",
    "\\jhat": "\\boldsymbol{\\hat{\\jmath}}",
    "\\khat": "\\boldsymbol{\\hat{k}}",
    "\\ehat": "\\boldsymbol{\\hat{e}}",
    "\\dott": "\\boldsymbol{\\cdot}",
    "\\leftrightarrow": "\\longleftrightarrow",
    "\\Leftrightarrow": "\\Longleftrightarrow",
};

const { renderInline, renderDisplay, renderTitle } = useKatex(macros);

const scrollContainer = ref<HTMLElement | null>(null);
const sidebarRef = ref<InstanceType<typeof PaperSidebar> | null>(null);
const sidebarNav = computed(() => sidebarRef.value?.sidebarNav ?? null);
const baseUrl = import.meta.env.BASE_URL;

// ── Build PaperContext and wire up tracking ────────────────
let _scrollTo: (id: string) => void = () => {};

const paperContext: PaperContext = {
    sections: paperSections,
    labelMap,
    renderInline,
    renderDisplay,
    renderTitle,
    assetBase: `${baseUrl}assets/`,
    scrollToId: (id) => _scrollTo(id),
};

provide(PAPER_CONTEXT, paperContext);

const {
    visibleCount,
    loadSentinel,
    treeIndex,
    isActive,
    isInActiveChain,
    activeId,
    activeRootId,
    scrollTo,
} = usePaperReader({
    context: paperContext,
    scrollContainer,
    sidebarEl: sidebarNav,
});

_scrollTo = scrollTo;

const sections = computed(() => paperSections);

function getPreview(section: PaperSectionData): string {
    const text = section.paragraphs?.[0] ?? "";
    const clean = text.replace(/\$[^$]+\$/g, "\u2026").replace(/<[^>]+>/g, "");
    const preview = clean.length > 100 ? clean.slice(0, 100) + "\u2026" : clean;

    const parts: string[] = [];
    if (preview) parts.push(preview);
    if (section.summary) parts.push(section.summary);

    return parts.join(" \u00b7 ");
}

// ── Mobile floating TOC visibility ───────────────────────────
const mobileNavRef = ref<HTMLElement | null>(null);
const mobileTocVisible = ref(true);
let mobileTocObserver: IntersectionObserver | null = null;

const currentSection = computed(() => {
    if (!activeRootId.value) return null;
    const entry = treeIndex.get(activeRootId.value);
    if (!entry) return null;
    return paperSections.find((s) => s.id === entry.node.id) ?? null;
});

onMounted(() => {
    mobileTocObserver = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                mobileTocVisible.value = entry.isIntersecting;
            }
        },
        { threshold: 0 },
    );
    nextTick(() => {
        if (mobileNavRef.value) mobileTocObserver!.observe(mobileNavRef.value);
    });
});

onUnmounted(() => {
    mobileTocObserver?.disconnect();
});
</script>

<template>
    <div ref="scrollContainer" class="paper-scroll">
        <!-- Mobile floating TOC bar -->
        <Transition name="slide-down">
            <MobileFloatingToc
                v-if="!mobileTocVisible"
                :sections="sections"
                :active-root-id="activeRootId"
                :current-section="currentSection"
                :scroll-to="scrollTo"
                :render-title="renderTitle"
                :scroll-container="scrollContainer"
            />
        </Transition>

        <div class="paper-layout mx-auto max-w-5xl px-2 py-2 sm:py-14 pb-4 sm:px-6">
            <div class="paper-grid">
                <!-- Desktop sidebar TOC -->
                <PaperSidebar
                    ref="sidebarRef"
                    :sections="sections"
                    :active-root-id="activeRootId"
                    :active-id="activeId"
                    :scroll-to="scrollTo"
                    :render-title="renderTitle"
                    :tree-index="treeIndex"
                    :is-active="isActive"
                    :is-in-active-chain="isInActiveChain"
                    :get-preview="getPreview"
                />

                <!-- Main article -->
                <article class="paper-article leading-relaxed">
                    <header class="mb-20 text-center">
                        <h1
                            class="cm-serif text-4xl font-bold tracking-tight sm:text-5xl md:text-[3.25rem] leading-[1.15]"
                        >
                            An Introduction to<br /><span class="fourier-f">ℱ</span>ourier Analysis
                        </h1>
                    </header>

                    <!-- Mobile-only inline TOC -->
                    <nav ref="mobileNavRef" class="mb-14 cm-serif text-sm text-muted-foreground lg:hidden">
                        <ol class="list-none space-y-1.5 pl-0">
                            <li v-for="section in sections" :key="section.id">
                                <button
                                    @click="scrollTo(section.id)"
                                    class="text-left hover:text-foreground transition-colors duration-150 cursor-pointer"
                                >
                                    <span>{{ section.number }}. </span><span v-html="renderTitle(section.title)" />
                                </button>
                            </li>
                        </ol>
                    </nav>

                    <PaperSectionContent
                        v-for="(section, si) in sections.slice(0, visibleCount)"
                        :key="section.id"
                        :section="section"
                        :depth="0"
                        :section-index="si"
                    >
                        <template #figure="{ figure }">
                            <img
                                :src="`${baseUrl}assets/${figure.filename}`"
                                :alt="figure.caption"
                                class="max-w-full rounded-lg shadow-sm"
                                :class="figure.filename.includes('portrait') ? 'paper-portrait' : 'paper-figure'"
                                style="max-height: 400px"
                                loading="lazy"
                            />
                        </template>
                        <template #callout="{ callout, section: sec }">
                            <div class="interactive-callout">
                                <p class="cm-serif text-sm text-muted-foreground mb-3">{{ callout.text }}</p>
                                <router-link
                                    :to="callout.link"
                                    class="callout-btn"
                                >
                                    <span class="fourier-f">ℱ</span>
                                    <span>Open Visualizer</span>
                                    <ArrowRight class="h-4 w-4" />
                                </router-link>
                            </div>
                        </template>
                    </PaperSectionContent>
                    <!-- Sentinel triggers loading next batch when scrolled near -->
                    <div
                        v-if="visibleCount < sections.length"
                        ref="loadSentinel"
                        class="load-sentinel"
                    >
                        <span class="text-muted-foreground/50 text-sm cm-serif">Loading…</span>
                    </div>
                    <!-- Bottom spacer so the last section can scroll fully into view -->
                    <div v-else class="last-section-spacer" />
                </article>
            </div>
        </div>
    </div>
</template>

<style scoped>
.paper-scroll {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    max-width: 100vw;
}

.paper-article {
    font-feature-settings: "liga", "kern";
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    hyphens: auto;
    min-width: 0;
    border-radius: 0.75rem;
    border: 2px solid hsl(var(--foreground) / 0.15);
    background: hsl(var(--card));
    box-shadow: 3px 3px 0px 0px hsl(var(--foreground) / 0.08);
    padding: 1.25rem 1rem;
    overflow-x: hidden;
    box-sizing: border-box;
}

@media (min-width: 640px) {
    .paper-article {
        padding: 2rem 2.5rem;
    }
}

.paper-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 2rem;
    min-width: 0;
}

@media (min-width: 1024px) {
    .paper-grid {
        grid-template-columns: 220px minmax(0, 48rem);
        gap: 2rem;
    }
}

.load-sentinel {
    display: flex;
    justify-content: center;
    padding: 2rem 0;
}

.last-section-spacer {
    height: 50vh;
}

/* ── Transition: slide-down ──────────────────────────────── */
.slide-down-enter-active,
.slide-down-leave-active {
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-down-enter-from {
    transform: translateY(-100%);
    opacity: 0;
}

.slide-down-leave-to {
    transform: translateY(-100%);
    opacity: 0;
}

/* Interactive callout */
.interactive-callout {
    margin: 1.5rem 0;
    padding: 1.25rem 1.5rem;
    border: 1px solid hsl(var(--border));
    border-radius: 0.75rem;
    background: hsl(var(--muted) / 0.25);
    text-align: center;
}

.callout-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.5rem;
    font-size: 0.9375rem;
    font-weight: 600;
    color: hsl(var(--primary-foreground));
    background: hsl(var(--primary));
    border-radius: 9999px;
    text-decoration: none;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 2px 8px hsl(var(--primary) / 0.25);
}

.callout-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px hsl(var(--primary) / 0.35);
}

.callout-btn .fourier-f {
    font-size: 1.1em;
    opacity: 0.85;
}
</style>

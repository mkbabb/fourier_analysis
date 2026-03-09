<script setup lang="ts">
import {
    PaperSectionContent,
    usePaperReader,
    useKatex,
    createRenderTitle,
    PAPER_CONTEXT,
    type PaperContext,
} from "@mkbabb/latex-paper/vue";
import "@mkbabb/latex-paper/theme";
import Tooltip from "@/components/ui/tooltip/Tooltip.vue";
import { paperSections, labelMap } from "@/lib/paperContent";
import type { PaperSectionData } from "@/lib/paperContent";
import { ref, computed, provide, watch, onMounted, onUnmounted, nextTick } from "vue";
import { ChevronDown, ArrowRight } from "lucide-vue-next";

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
const sidebarNav = ref<HTMLElement | null>(null);
const baseUrl = import.meta.env.BASE_URL;

// ── Build PaperContext and wire up tracking ────────────────
// scrollToId is a late-bound reference set after usePaperReader creates scrollTo
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

// ── Mobile floating TOC ─────────────────────────────────────
const mobileNavRef = ref<HTMLElement | null>(null);
const mobileTocVisible = ref(true);
const floatingTocOpen = ref(false);
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

watch(activeRootId, () => {
    floatingTocOpen.value = false;
});
</script>

<template>
    <div ref="scrollContainer" class="paper-scroll">
        <!-- Mobile floating TOC bar -->
        <Transition name="slide-down">
            <div v-if="!mobileTocVisible" class="floating-toc lg:hidden">
                <button class="floating-toc-bar" @click="floatingTocOpen = !floatingTocOpen">
                    <span class="floating-toc-section cm-serif">
                        <span class="fira-code text-xs opacity-50">{{ currentSection?.number }}.</span>
                        {{ currentSection?.title }}
                    </span>
                    <ChevronDown class="floating-toc-chevron" :class="{ 'rotate-180': floatingTocOpen }" />
                </button>
                <Transition name="toc-expand">
                    <div v-if="floatingTocOpen" class="floating-toc-dropdown">
                        <button
                            v-for="(section, si) in sections"
                            :key="section.id"
                            class="floating-toc-item cm-serif"
                            :class="{ 'is-active': activeRootId === section.id }"
                            :style="activeRootId === section.id ? { color: `var(--section-color-${si})` } : {}"
                            @click="scrollTo(section.id); floatingTocOpen = false"
                        >
                            <span class="fira-code text-xs opacity-50">{{ section.number }}.</span>
                            {{ section.title }}
                        </button>
                    </div>
                </Transition>
            </div>
        </Transition>

        <div class="paper-layout mx-auto max-w-5xl px-2 py-14 pb-4 sm:px-6">
            <div class="paper-grid">
                <!-- Desktop sidebar TOC -->
                <aside class="paper-sidebar">
                    <nav ref="sidebarNav" class="sidebar-nav scrollbar-thin">
                        <p class="sidebar-label cm-serif">Contents</p>
                        <ol class="sidebar-list">
                            <li v-for="(section, si) in sections" :key="section.id">
                                <Tooltip :text="getPreview(section)" side="right">
                                    <button
                                        :data-toc-id="section.id"
                                        @click="scrollTo(section.id)"
                                        class="sidebar-link cm-serif"
                                        :class="{ 'is-active': activeRootId === section.id }"
                                        :style="activeRootId === section.id ? { color: `var(--section-color-${si})` } : {}"
                                    >
                                        <span class="sidebar-number fira-code">{{ section.number }}.</span>
                                        <span v-html="renderTitle(section.title)" />
                                    </button>
                                </Tooltip>
                                <!-- Subsections (animated expand) -->
                                <div
                                    v-if="section.subsections"
                                    class="sidebar-sublist-wrapper"
                                    :class="{ 'is-expanded': activeRootId === section.id }"
                                >
                                    <ol class="sidebar-sublist">
                                        <li v-for="sub in section.subsections" :key="sub.id">
                                            <Tooltip :text="getPreview(sub)" side="right">
                                                <button
                                                    :data-toc-id="sub.id"
                                                    @click="scrollTo(sub.id)"
                                                    class="sidebar-link sidebar-sublink cm-serif"
                                                    :class="{ 'is-active-sub': isActive(sub.id, activeId) || isInActiveChain(sub.id, activeId) }"
                                                    :style="isActive(sub.id, activeId)
                                                        ? { color: `var(--section-color-${si})`, fontWeight: '600', background: 'hsl(var(--muted) / 0.4)' }
                                                        : isInActiveChain(sub.id, activeId)
                                                            ? { color: `color-mix(in srgb, var(--section-color-${si}) 70%, hsl(var(--muted-foreground)))` }
                                                            : activeRootId === section.id
                                                                ? { color: `color-mix(in srgb, var(--section-color-${si}) 50%, hsl(var(--muted-foreground)))` }
                                                                : {}"
                                                >
                                                    <span class="sidebar-number fira-code">{{ sub.number }}.</span>
                                                    <span v-html="renderTitle(sub.title)" />
                                                </button>
                                            </Tooltip>
                                            <!-- Sub-subsections -->
                                            <ol v-if="sub.subsections && isInActiveChain(sub.id, activeId)" class="sidebar-subsublist">
                                                <li v-for="subsub in sub.subsections" :key="subsub.id">
                                                    <button
                                                        :data-toc-id="subsub.id"
                                                        @click="scrollTo(subsub.id)"
                                                        class="sidebar-link sidebar-subsublink cm-serif"
                                                        :style="isActive(subsub.id, activeId)
                                                            ? { color: `var(--section-color-${si})`, fontWeight: '600', background: 'hsl(var(--muted) / 0.4)' }
                                                            : { color: `color-mix(in srgb, var(--section-color-${si}) 40%, hsl(var(--muted-foreground)))` }"
                                                    >
                                                        <span class="sidebar-number fira-code">{{ subsub.number }}.</span>
                                                        <span v-html="renderTitle(subsub.title)" />
                                                    </button>
                                                </li>
                                            </ol>
                                        </li>
                                    </ol>
                                </div>
                            </li>
                        </ol>
                    </nav>
                </aside>

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

.paper-sidebar {
    display: none;
}

@media (min-width: 1024px) {
    .paper-sidebar {
        display: block;
    }
}

.sidebar-nav {
    position: sticky;
    top: 1.5rem;
    max-height: calc(100dvh - 5rem);
    overflow-y: auto;
    padding: 0.75rem;
    border-radius: 0.75rem;
    border: 2px solid hsl(var(--foreground) / 0.15);
    background: hsl(var(--card));
    box-shadow: 3px 3px 0px 0px hsl(var(--foreground) / 0.08);
}

.sidebar-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: hsl(var(--muted-foreground) / 0.6);
    padding: 0 0.75rem;
    margin-bottom: 0.75rem;
}

.sidebar-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
}

.sidebar-link {
    display: block;
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1.45;
    padding: 0.375rem 0.75rem;
    border-radius: calc(var(--radius) - 2px);
    color: hsl(var(--muted-foreground));
    transition: color 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                background-color 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                font-weight 0.15s ease;
}

.sidebar-link:hover {
    color: hsl(var(--foreground));
    background: hsl(var(--muted) / 0.5);
}

.sidebar-link.is-active {
    background: none;
    font-weight: 600;
}

.sidebar-number {
    font-size: 0.75rem;
    margin-right: 0.25rem;
    opacity: 0.5;
}

.sidebar-link.is-active .sidebar-number {
    opacity: 0.8;
}

/* Animated subsection expand/collapse */
.sidebar-sublist-wrapper {
    display: grid;
    grid-template-rows: 0fr;
    opacity: 0;
    transition: grid-template-rows 0.4s cubic-bezier(0.16, 1, 0.3, 1),
                opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.sidebar-sublist-wrapper.is-expanded {
    grid-template-rows: 1fr;
    opacity: 1;
}

.sidebar-sublist-wrapper > .sidebar-sublist {
    overflow: hidden;
}

.sidebar-sublist {
    list-style: none;
    padding: 0 0 0 0.75rem;
    margin: 0.125rem 0 0.25rem;
}

.sidebar-sublink {
    font-size: 0.8125rem;
    padding: 0.25rem 0.5rem;
}

.sidebar-subsublist {
    list-style: none;
    padding: 0 0 0 0.625rem;
    margin: 0.0625rem 0 0.125rem;
}

.sidebar-subsublink {
    font-size: 0.75rem;
    padding: 0.1875rem 0.375rem;
}

.load-sentinel {
    display: flex;
    justify-content: center;
    padding: 2rem 0;
}

.last-section-spacer {
    height: 50vh;
}

/* ── Mobile floating TOC bar ───────────────────────────────── */
.floating-toc {
    position: sticky;
    top: 0;
    z-index: 20;
    padding: 0 0.5rem;
}

.floating-toc-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0.625rem 1rem;
    background: hsl(var(--background) / 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: none;
    border-bottom: 1px solid hsl(var(--border) / 0.5);
    cursor: pointer;
    text-align: left;
    font-size: 0.875rem;
    font-weight: 500;
    color: hsl(var(--foreground));
}

.floating-toc-section {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
}

.floating-toc-chevron {
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
    opacity: 0.5;
    transition: transform 0.2s ease;
}

.floating-toc-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: hsl(var(--background) / 0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid hsl(var(--border));
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    max-height: 60vh;
    overflow-y: auto;
    padding: 0.5rem;
}

.floating-toc-item {
    display: block;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    border: none;
    background: none;
    cursor: pointer;
    text-align: left;
    font-size: 0.8125rem;
    color: hsl(var(--muted-foreground));
    transition: all 0.15s;
}

.floating-toc-item:hover,
.floating-toc-item.is-active {
    background: hsl(var(--muted) / 0.5);
    color: hsl(var(--foreground));
}

.floating-toc-item.is-active {
    font-weight: 600;
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

/* ── Transition: toc-expand ──────────────────────────────── */
.toc-expand-enter-active,
.toc-expand-leave-active {
    transition: opacity 0.2s ease,
                transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.toc-expand-enter-from {
    opacity: 0;
    transform: translateY(-0.5rem);
}

.toc-expand-leave-to {
    opacity: 0;
    transform: translateY(-0.5rem);
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

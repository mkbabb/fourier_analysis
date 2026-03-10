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
import { ref, reactive, computed, provide, onMounted, onUnmounted, nextTick } from "vue";
import { ArrowRight, Undo2 } from "lucide-vue-next";

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
    scrollTo: rawScrollTo,
    forceRecalculate,
} = usePaperReader({
    context: paperContext,
    scrollContainer,
    sidebarEl: sidebarNav,
});

// ── Scroll navigation ─────────────────────────────────────────
const TELEPORT_THRESHOLD = 1200;

/** Dynamic scroll offset: accounts for floating TOC bar on mobile */
function getScrollOffset(): number {
    const bar = document.querySelector('.floating-toc-bar') as HTMLElement | null;
    if (bar) return bar.offsetHeight + 8;
    return 16;
}

function ensureTargetLoaded(id: string) {
    const entry = treeIndex.get(id);
    if (entry) {
        const needed = entry.rootIndex + 2;
        visibleCount.value = Math.max(
            visibleCount.value,
            Math.min(needed, paperSections.length),
        );
    } else {
        visibleCount.value = paperSections.length;
    }
}

/**
 * Overlay-based teleport: covers content, jumps, corrects until layout
 * stabilizes, then reveals.  Content rendering (images, math) can shift
 * the target element for several frames after Vue mounts new sections.
 */
function teleportTo(sc: HTMLElement, target: HTMLElement | null, offset: number, scrollTop?: number) {
    const overlay = sc.querySelector('.teleport-overlay') as HTMLElement | null;

    const jumpOnce = () => {
        if (target) {
            target.scrollIntoView({ behavior: "instant", block: "start" });
            sc.scrollBy({ top: -offset, behavior: "instant" });
        } else if (scrollTop !== undefined) {
            sc.scrollTo({ top: scrollTop, behavior: "instant" });
        }
    };

    /** Keep re-scrolling to target until scrollHeight stops changing. */
    const jumpUntilStable = (onDone: () => void) => {
        let lastHeight = -1;
        let stableFrames = 0;
        const correct = () => {
            jumpOnce();
            const h = sc.scrollHeight;
            if (Math.abs(h - lastHeight) < 2) {
                if (++stableFrames >= 5) { onDone(); return; }
            } else {
                stableFrames = 0;
            }
            lastHeight = h;
            requestAnimationFrame(correct);
        };
        correct();
    };

    if (!overlay) {
        jumpUntilStable(() => forceRecalculate());
        return;
    }

    // Phase 1: fade overlay in
    overlay.style.transition = "opacity 80ms ease-out";
    overlay.style.opacity = "1";
    overlay.style.pointerEvents = "auto";

    let started = false;
    const startJump = () => {
        if (started) return;
        started = true;

        // Phase 2: jump + correct while overlay hides everything
        jumpUntilStable(() => {
            forceRecalculate();
            // Phase 3: reveal
            requestAnimationFrame(() => {
                overlay.style.transition = "opacity 120ms ease-in";
                overlay.style.opacity = "0";
                overlay.style.pointerEvents = "none";
            });
        });
    };

    overlay.addEventListener("transitionend", startJump, { once: true });
    setTimeout(startJump, 120);
}

function performScroll(id: string) {
    const scroller = scrollContainer.value;
    if (!scroller) { rawScrollTo(id); return; }

    ensureTargetLoaded(id);

    let attempts = 0;
    function tryNavigate() {
        const el = document.getElementById(id);
        const s = scrollContainer.value;
        if (!el || !s) {
            if (attempts++ < 60) requestAnimationFrame(tryNavigate);
            return;
        }

        const elRect = el.getBoundingClientRect();
        const scrollerRect = s.getBoundingClientRect();
        const offset = getScrollOffset();
        const distance = Math.abs(elRect.top - scrollerRect.top);

        if (distance < TELEPORT_THRESHOLD) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
            s.scrollBy({ top: -offset, behavior: "smooth" });
            return;
        }

        // Far — overlay fade, teleport, reveal
        teleportTo(s, el, offset);
    }

    nextTick(() => requestAnimationFrame(tryNavigate));
}

// ── Navigation stack (Kindle-style back traversal) ────────────
const MAX_STACK = 20;
const navStack = reactive<string[]>([]);
let isBackNavigation = false;

/** Navigate to a section, pushing current position to the back stack */
function navigateTo(id: string) {
    if (!isBackNavigation && activeId.value && activeId.value !== id) {
        navStack.push(activeId.value);
        if (navStack.length > MAX_STACK) navStack.shift();
    }
    performScroll(id);
}

/** Pop the navigation stack and scroll back */
function navigateBack() {
    if (navStack.length === 0) return;
    isBackNavigation = true;
    const prev = navStack.pop()!;
    performScroll(prev);
    setTimeout(() => { isBackNavigation = false; }, 500);
}

/** Scroll to top of paper */
function scrollToTop() {
    const s = scrollContainer.value;
    if (!s) return;
    if (s.scrollTop > TELEPORT_THRESHOLD) {
        teleportTo(s, null, 0, 0);
    } else {
        s.scrollTo({ top: 0, behavior: "smooth" });
    }
}

// Wire all navigation (TOC clicks, cross-references) through navigateTo
_scrollTo = navigateTo;

const sections = computed(() => paperSections);

function getPreview(section: PaperSectionData): string {
    const text = section.content?.find((b): b is string => typeof b === "string") ?? "";
    const clean = text.replace(/\$[^$]+\$/g, "\u2026").replace(/<[^>]+>/g, "");
    const preview = clean.length > 100 ? clean.slice(0, 100) + "\u2026" : clean;

    const parts: string[] = [];
    if (preview) parts.push(preview);
    if (section.summary) parts.push(section.summary);

    return parts.join(" \u00b7 ");
}

// ── Page number estimation from LaTeX content ─────────────────
const pageMap = new Map<string, number>();
let _cumPage = 1;
function walkPages(secs: PaperSectionData[]) {
    for (const sec of secs) {
        pageMap.set(sec.id, Math.ceil(_cumPage));
        const blocks = (sec.content?.length ?? 0)
            + (sec.theorems?.length ?? 0) * 1.2
            + (sec.figures?.length ?? 0) * 1.5;
        _cumPage += blocks / 3;
        if (sec.subsections) walkPages(sec.subsections);
    }
}
walkPages(paperSections);
const totalPages = Math.max(1, Math.ceil(_cumPage - 1));

const currentPage = computed(() => {
    const id = activeId.value;
    if (!id) return 1;
    return pageMap.get(id) ?? 1;
});

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
    <div class="paper-root">
        <div ref="scrollContainer" class="paper-scroll">
            <div class="teleport-overlay" />
            <!-- Mobile floating TOC bar -->
            <Transition name="slide-down">
                <MobileFloatingToc
                    v-if="!mobileTocVisible"
                    :sections="sections"
                    :active-root-id="activeRootId"
                    :current-section="currentSection"
                    :scroll-to="navigateTo"
                    :scroll-to-top="scrollToTop"
                    :render-title="renderTitle"
                    :scroll-container="scrollContainer"
                />
            </Transition>

            <div class="paper-layout mx-auto max-w-5xl px-2 pt-2 pb-0 sm:py-14 sm:px-6">
                <div class="paper-grid">
                    <!-- Desktop sidebar TOC -->
                    <PaperSidebar
                        ref="sidebarRef"
                        :sections="sections"
                        :active-root-id="activeRootId"
                        :active-id="activeId"
                        :scroll-to="navigateTo"
                        :scroll-to-top="scrollToTop"
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
                                        @click="navigateTo(section.id)"
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

        <!-- Bottom overlay: page indicator (left) + back button (right) -->
        <div class="paper-bottom-overlay">
            <div class="overlay-page fira-code">
                pg {{ currentPage }}<span class="overlay-page-sep">/</span>{{ totalPages }}
            </div>

            <Transition name="fade-scale">
                <button
                    v-if="navStack.length > 0"
                    class="overlay-btn overlay-back"
                    @click="navigateBack"
                    :title="`Back (${navStack.length} in history)`"
                >
                    <Undo2 class="h-3.5 w-3.5" />
                    <span v-if="navStack.length > 1" class="overlay-badge">{{ navStack.length }}</span>
                </button>
            </Transition>
        </div>
    </div>
</template>

<style scoped>
.paper-root {
    position: relative;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

.paper-scroll {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    max-width: 100vw;
}

.teleport-overlay {
    position: fixed;
    inset: 0;
    z-index: 50;
    background: hsl(var(--background));
    opacity: 0;
    pointer-events: none;
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

/* ── Bottom overlay ────────────────────────────────────────── */
.paper-bottom-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 15;
    pointer-events: none;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 0.75rem 1rem;
    padding-bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px));
}

.overlay-btn {
    pointer-events: auto;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    border: 1.5px solid hsl(var(--border));
    background: hsl(var(--background) / 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: hsl(var(--foreground) / 0.7);
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.overlay-btn:hover {
    color: hsl(var(--foreground));
    border-color: hsl(var(--foreground) / 0.25);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    transform: scale(1.05);
}

.overlay-btn:active {
    transform: scale(0.95);
}

.overlay-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    min-width: 16px;
    height: 16px;
    border-radius: 8px;
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    font-size: 0.625rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 3px;
    line-height: 1;
}

.overlay-page {
    pointer-events: auto;
    font-size: 0.6875rem;
    color: hsl(var(--muted-foreground) / 0.7);
    background: hsl(var(--background) / 0.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid hsl(var(--border) / 0.5);
    border-radius: 0.375rem;
    padding: 0.25rem 0.5rem;
    letter-spacing: 0.02em;
    user-select: none;
}

.overlay-page-sep {
    opacity: 0.4;
    margin: 0 1px;
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

/* ── Transition: fade-scale (back button) ─────────────────── */
.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-scale-enter-from {
    opacity: 0;
    transform: scale(0.8);
}

.fade-scale-leave-to {
    opacity: 0;
    transform: scale(0.8);
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

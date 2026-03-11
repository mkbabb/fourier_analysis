<script setup lang="ts">
import {
    useKatex,
    PAPER_CONTEXT,
    type PaperContext,
    flattenPaperSections,
    useClickDelegate,
    useSidebarFollow,
    useTreeIndex,
    useVirtualSectionWindow,
} from "@mkbabb/latex-paper/vue";
import "@mkbabb/latex-paper/theme";
import PaperSidebar from "./PaperSidebar.vue";
import MobileFloatingToc from "./MobileFloatingToc.vue";
import PaperArticleWindow from "./PaperArticleWindow.vue";
import { getPaperPreview, paperSectionToTreeNode } from "./paperTree";
import { useScrollNavigation } from "./useScrollNavigation";
import { paperSections, labelMap, totalPages, pageMap } from "@/lib/paperContent";
import type { PaperSectionData } from "@/lib/paperContent";
import { ref, computed, provide, onMounted, onUnmounted, nextTick, watch } from "vue";
import { Undo2 } from "lucide-vue-next";

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
const sectionWindowRoot = ref<HTMLElement | null>(null);
const sectionStartOffsetPx = ref(0);
const sidebarRef = ref<InstanceType<typeof PaperSidebar> | null>(null);
const baseUrl = import.meta.env.BASE_URL;
const flatSections = flattenPaperSections(paperSections);
const treeNodes = paperSections.map(paperSectionToTreeNode);
const { index: treeIndex, isActive, isInActiveChain } = useTreeIndex(treeNodes);

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
    visibleItems,
    topSpacerPx,
    bottomSpacerPx,
    measureSection,
    ensureTargetWindow,
    getOffsetFor,
    activeId,
    activeRootId,
    recalculate,
} = useVirtualSectionWindow({
    items: flatSections,
    scrollContainer,
    overscanBeforePx: 240,
    overscanAfterPx: 720,
    leadingOffsetPx: sectionStartOffsetPx,
    warmTargetBefore: 2,
    warmTargetAfter: 3,
});

useClickDelegate({
    container: scrollContainer,
    selector: ".paper-ref",
    attribute: "data-ref",
    resolve: (refKey) => {
        const info = labelMap[refKey];
        if (!info) return null;
        return info.elementId ?? info.sectionId;
    },
    scrollTo: (id) => _scrollTo(id),
});

const { navigateTo, navigateBack, scrollToTop, navStack } = useScrollNavigation({
    scrollContainer,
    contentStartOffsetPx: sectionStartOffsetPx,
    activeId,
    ensureTargetWindow,
    getOffsetFor,
    recalculate,
});

// Wire all navigation (TOC clicks, cross-references) through navigateTo
_scrollTo = navigateTo;

const sections = computed(() => paperSections);
const currentPage = ref(pageMap[flatSections[0]?.id] ?? 1);

watch(
    activeId,
    (id) => {
        if (!id) return;
        const page = pageMap[id];
        if (page !== undefined) currentPage.value = page;
    },
    { immediate: true },
);

// ── Mobile floating TOC visibility ───────────────────────────
const mobileNavRef = ref<HTMLElement | null>(null);
const mobileTocVisible = ref(true);
let mobileTocObserver: IntersectionObserver | null = null;

function updateSectionStartOffset() {
    const root = sectionWindowRoot.value;
    const scroller = scrollContainer.value;
    if (!root || !scroller) return;
    sectionStartOffsetPx.value =
        root.getBoundingClientRect().top -
        scroller.getBoundingClientRect().top +
        scroller.scrollTop;
}

function registerWindowRoot(el: HTMLElement | null) {
    if (sectionWindowRoot.value === el) return;
    sectionWindowRoot.value = el;
    if (!el) return;
    nextTick(() => {
        updateSectionStartOffset();
        recalculate();
    });
}

function handleWindowResize() {
    updateSectionStartOffset();
    recalculate();
}

const sidebarNavEl = computed(() => sidebarRef.value?.sidebarNav ?? null);
const { queueSidebarFollow } = useSidebarFollow({
    sidebarEl: sidebarNavEl,
    activeId,
    activeRootId,
    scrollSource: scrollContainer,
});

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
        updateSectionStartOffset();
        recalculate();
        queueSidebarFollow(true);
    });
    window.addEventListener("resize", handleWindowResize);
});

watch([scrollContainer, sectionWindowRoot], ([scroller, root]) => {
    if (!scroller || !root) {
        updateSectionStartOffset();
        return;
    }
    updateSectionStartOffset();
    nextTick(() => {
        recalculate();
        queueSidebarFollow(true);
    });
});

onUnmounted(() => {
    mobileTocObserver?.disconnect();
    window.removeEventListener("resize", handleWindowResize);
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
                        :get-preview="getPaperPreview"
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

                        <PaperArticleWindow
                            :visible-items="visibleItems"
                            :top-spacer-px="topSpacerPx"
                            :bottom-spacer-px="bottomSpacerPx"
                            :register-root="registerWindowRoot"
                            :measure-section="measureSection"
                        />
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
    transition: opacity 120ms cubic-bezier(0.16, 1, 0.3, 1);
    will-change: opacity;
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
</style>

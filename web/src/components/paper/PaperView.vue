<script setup lang="ts">
import PaperSectionContent from "./PaperSectionContent.vue";
import { paperSections } from "@/lib/paperContent";
import type { PaperSectionData } from "@/lib/paperContent";
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";

const sections = computed(() => paperSections);

// ── Progressive loading: mount sections as they approach viewport ──
const visibleCount = ref(2); // start with first 2 sections rendered
const loadSentinel = ref<HTMLElement | null>(null);
let loadObserver: IntersectionObserver | null = null;

onMounted(() => {
    loadObserver = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting && visibleCount.value < paperSections.length) {
                    visibleCount.value = Math.min(visibleCount.value + 2, paperSections.length);
                }
            }
        },
        { rootMargin: "0px 0px 600px 0px" },
    );
    nextTick(() => {
        if (loadSentinel.value) loadObserver!.observe(loadSentinel.value);
    });
});

onUnmounted(() => {
    loadObserver?.disconnect();
});

// Re-observe the sentinel when it moves (after new sections mount)
watch(visibleCount, () => {
    if (!loadObserver) return;
    loadObserver.disconnect();
    nextTick(() => {
        if (loadSentinel.value) loadObserver!.observe(loadSentinel.value);
    });
});

// ── Build a flat index of ALL sections at every depth ──────
interface TocEntry {
    section: PaperSectionData;
    depth: number;
    parentId: string | null; // top-level parent id
    topIndex: number;       // top-level section index (for color)
}

const tocIndex = new Map<string, TocEntry>();

function indexSections(
    list: PaperSectionData[],
    depth: number,
    parentId: string | null,
    topIndex: number,
) {
    for (const s of list) {
        const ti = depth === 0 ? list.indexOf(s) : topIndex;
        tocIndex.set(s.id, { section: s, depth, parentId: depth === 0 ? s.id : parentId, topIndex: ti });
        if (s.subsections) {
            indexSections(s.subsections, depth + 1, depth === 0 ? s.id : parentId, ti);
        }
    }
}
indexSections(paperSections, 0, null, 0);

// ── Scroll-tracked active section ──────────────────────────
const activeId = ref<string | null>(paperSections[0]?.id ?? null);
let observer: IntersectionObserver | null = null;
const sectionVisibility = new Map<string, boolean>();

/** Walk the tree bottom-up: the deepest visible section wins. */
function findDeepestVisible(list: PaperSectionData[]): string | null {
    for (const s of list) {
        if (s.subsections) {
            const deep = findDeepestVisible(s.subsections);
            if (deep) return deep;
        }
        if (sectionVisibility.get(s.id)) return s.id;
    }
    return null;
}

function updateActive() {
    const found = findDeepestVisible(paperSections);
    if (found) activeId.value = found;
}

// Derived: which top-level section is active?
const activeTopId = computed(() => {
    if (!activeId.value) return null;
    return tocIndex.get(activeId.value)?.parentId ?? null;
});

// Which IDs are "active" at any level? (the active item + all its ancestors)
function isActive(id: string): boolean {
    return id === activeId.value;
}

function isInActiveChain(id: string): boolean {
    if (!activeId.value) return false;
    const entry = tocIndex.get(activeId.value);
    if (!entry) return false;
    // Check if id is the active item or its top-level parent
    if (id === activeId.value) return true;
    if (id === entry.parentId) return true;
    // Check if activeId is a descendant of id
    // Walk the section's subsections
    const target = tocIndex.get(id);
    if (!target) return false;
    return isDescendant(activeId.value, id);
}

function isDescendant(childId: string, ancestorId: string): boolean {
    const ancestor = tocIndex.get(ancestorId);
    if (!ancestor) return false;
    const section = ancestor.section;
    if (!section.subsections) return false;
    for (const sub of section.subsections) {
        if (sub.id === childId) return true;
        if (sub.subsections && isDescendant(childId, sub.id)) return true;
    }
    return false;
}

// ── Observe section elements for scroll tracking ──────────
const observedIds = new Set<string>();

function observeTree(list: PaperSectionData[]) {
    for (const s of list) {
        if (!observedIds.has(s.id)) {
            const el = document.getElementById(s.id);
            if (el) {
                observer!.observe(el);
                observedIds.add(s.id);
            }
        }
        if (s.subsections) observeTree(s.subsections);
    }
}

onMounted(() => {
    observer = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                sectionVisibility.set(
                    (entry.target as HTMLElement).id,
                    entry.isIntersecting,
                );
            }
            updateActive();
        },
        { rootMargin: "-20% 0px -60% 0px", threshold: 0 },
    );
    nextTick(() => observeTree(paperSections));
});

onUnmounted(() => {
    observer?.disconnect();
});

// Re-observe when new sections mount from progressive loading
watch(visibleCount, () => {
    if (!observer) return;
    nextTick(() => observeTree(paperSections));
});

// ── Auto-scroll sidebar to keep active item visible ────────
const sidebarNav = ref<HTMLElement | null>(null);

watch(activeId, (id) => {
    if (!id || !sidebarNav.value) return;
    nextTick(() => {
        const el = sidebarNav.value?.querySelector(`[data-toc-id="${id}"]`) as HTMLElement | null;
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    });
});

function scrollToSection(id: string) {
    // Ensure the section is loaded before scrolling
    const entry = tocIndex.get(id);
    if (entry) {
        const topIdx = paperSections.indexOf(
            paperSections.find(s => s.id === entry.parentId) ?? paperSections[0]
        );
        if (topIdx >= 0 && topIdx >= visibleCount.value) {
            visibleCount.value = Math.min(topIdx + 2, paperSections.length);
        }
    }
    nextTick(() => {
        const el = document.getElementById(id);
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
}

function getPreview(section: PaperSectionData): string {
    const text = section.paragraphs?.[0] ?? '';
    const clean = text.replace(/\$[^$]+\$/g, '…').replace(/<[^>]+>/g, '');
    return clean.length > 120 ? clean.slice(0, 120) + '…' : clean;
}
</script>

<template>
    <div class="paper-scroll">
        <div class="paper-layout mx-auto max-w-5xl px-2 py-14 pb-32 sm:px-6">
            <div class="paper-grid">
                <!-- Desktop sidebar TOC -->
                <aside class="paper-sidebar">
                    <nav ref="sidebarNav" class="sidebar-nav scrollbar-thin">
                        <p class="sidebar-label cm-serif">Contents</p>
                        <ol class="sidebar-list">
                            <li v-for="(section, si) in sections" :key="section.id">
                                <button
                                    :data-toc-id="section.id"
                                    @click="scrollToSection(section.id)"
                                    class="sidebar-link cm-serif"
                                    :class="{ 'is-active': activeTopId === section.id }"
                                    :style="activeTopId === section.id ? { color: `var(--section-color-${si})` } : {}"
                                    :title="getPreview(section)"
                                >
                                    <span class="sidebar-number fira-code">{{ section.number }}.</span>
                                    {{ section.title }}
                                </button>
                                <!-- Subsections (animated expand) -->
                                <div
                                    v-if="section.subsections"
                                    class="sidebar-sublist-wrapper"
                                    :class="{ 'is-expanded': activeTopId === section.id }"
                                >
                                    <ol class="sidebar-sublist">
                                        <li v-for="sub in section.subsections" :key="sub.id">
                                            <button
                                                :data-toc-id="sub.id"
                                                @click="scrollToSection(sub.id)"
                                                class="sidebar-link sidebar-sublink cm-serif"
                                                :class="{ 'is-active-sub': isActive(sub.id) || isInActiveChain(sub.id) }"
                                                :style="isActive(sub.id)
                                                    ? { color: `var(--section-color-${si})`, fontWeight: '600', background: 'hsl(var(--muted) / 0.4)' }
                                                    : isInActiveChain(sub.id)
                                                        ? { color: `color-mix(in srgb, var(--section-color-${si}) 70%, hsl(var(--muted-foreground)))` }
                                                        : activeTopId === section.id
                                                            ? { color: `color-mix(in srgb, var(--section-color-${si}) 50%, hsl(var(--muted-foreground)))` }
                                                            : {}"
                                                :title="getPreview(sub)"
                                            >
                                                <span class="sidebar-number fira-code">{{ sub.number }}.</span>
                                                {{ sub.title }}
                                            </button>
                                            <!-- Sub-subsections -->
                                            <ol v-if="sub.subsections && isInActiveChain(sub.id)" class="sidebar-subsublist">
                                                <li v-for="subsub in sub.subsections" :key="subsub.id">
                                                    <button
                                                        :data-toc-id="subsub.id"
                                                        @click="scrollToSection(subsub.id)"
                                                        class="sidebar-link sidebar-subsublink cm-serif"
                                                        :style="isActive(subsub.id)
                                                            ? { color: `var(--section-color-${si})`, fontWeight: '600', background: 'hsl(var(--muted) / 0.4)' }
                                                            : { color: `color-mix(in srgb, var(--section-color-${si}) 40%, hsl(var(--muted-foreground)))` }"
                                                    >
                                                        <span class="sidebar-number fira-code">{{ subsub.number }}.</span>
                                                        {{ subsub.title }}
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
                    <nav class="mb-14 cm-serif text-sm text-muted-foreground lg:hidden">
                        <ol class="list-none space-y-1.5 pl-0">
                            <li v-for="section in sections" :key="section.id">
                                <button
                                    @click="scrollToSection(section.id)"
                                    class="text-left hover:text-foreground transition-colors duration-150 cursor-pointer"
                                >
                                    {{ section.number }}. {{ section.title }}
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
                    />
                    <!-- Sentinel triggers loading next batch when scrolled near -->
                    <div
                        v-if="visibleCount < sections.length"
                        ref="loadSentinel"
                        class="load-sentinel"
                    >
                        <span class="text-muted-foreground/50 text-sm cm-serif">Loading…</span>
                    </div>
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
    width: 100%;
    max-width: 48rem;
    min-width: 0;
    margin: 0 auto;
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
        grid-template-columns: 220px 1fr;
        gap: 3rem;
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
</style>

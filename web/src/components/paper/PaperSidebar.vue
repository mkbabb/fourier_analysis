<script setup lang="ts">
import Tooltip from "@/components/ui/tooltip/Tooltip.vue";
import type { PaperSectionData } from "@/lib/paperContent";

import { ref } from "vue";

const props = defineProps<{
    sections: PaperSectionData[];
    activeRootId: string | null;
    activeId: string | null;
    scrollTo: (id: string) => void;
    renderTitle: (title: string) => string;
    treeIndex: Map<string, any>;
    isActive: (id: string, activeId: string | null) => boolean;
    isInActiveChain: (id: string, activeId: string | null) => boolean;
    getPreview: (section: PaperSectionData) => string;
}>();

const sidebarNav = ref<HTMLElement | null>(null);
defineExpose({ sidebarNav });
</script>

<template>
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
</template>

<style scoped>
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
</style>

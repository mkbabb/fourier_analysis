<script setup lang="ts">
import {
    PaperSection,
    PaperSectionBlocks,
    type FlatPaperSection,
} from "@mkbabb/latex-paper/vue";
import type { ComponentPublicInstance } from "vue";
import { ArrowRight } from "lucide-vue-next";

const props = defineProps<{
    visibleItems: FlatPaperSection[];
    topSpacerPx: number;
    bottomSpacerPx: number;
    registerRoot: (el: HTMLElement | null) => void;
    measureSection: (id: string, el: HTMLElement | null) => void;
}>();

const baseUrl = import.meta.env.BASE_URL;

function toHTMLElement(
    value: Element | ComponentPublicInstance | null,
): HTMLElement | null {
    return value instanceof HTMLElement ? value : null;
}

function bindRoot(value: Element | ComponentPublicInstance | null) {
    props.registerRoot(toHTMLElement(value));
}

function bindSection(
    id: string,
    value: Element | ComponentPublicInstance | null,
) {
    props.measureSection(id, toHTMLElement(value));
}
</script>

<template>
    <div :ref="bindRoot" class="paper-window-root">
        <div
            v-if="topSpacerPx > 0"
            class="paper-window-spacer"
            :style="{ height: `${topSpacerPx}px` }"
        />

        <div
            v-for="item in visibleItems"
            :key="item.id"
            :ref="(el) => bindSection(item.id, el)"
            class="paper-window-section"
        >
            <PaperSection
                :id="item.id"
                :number="item.section.number"
                :title="item.section.title"
                :depth="item.depth"
                :section-index="item.rootIndex"
            >
                <PaperSectionBlocks :section="item.section">
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
                    <template #callout="{ callout }">
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
                </PaperSectionBlocks>
            </PaperSection>
        </div>

        <div
            v-if="bottomSpacerPx > 0"
            class="paper-window-spacer"
            :style="{ height: `${bottomSpacerPx}px` }"
        />
        <div class="paper-window-footer-spacer" />
    </div>
</template>

<style scoped>
.paper-window-root {
    min-width: 0;
}

.paper-window-section {
    min-width: 0;
}

.paper-window-spacer {
    width: 100%;
    pointer-events: none;
}

.paper-window-footer-spacer {
    height: 50vh;
}

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

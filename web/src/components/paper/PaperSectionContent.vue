<script setup lang="ts">
import MathBlock from "./MathBlock.vue";
import PaperSection from "./PaperSection.vue";
import Theorem from "./Theorem.vue";
import { ArrowRight } from "lucide-vue-next";
import type { PaperSectionData } from "@/lib/paperContent";
import { useKatex } from "@/composables/useKatex";

const props = defineProps<{
    section: PaperSectionData;
    depth: number;
    sectionIndex: number; // top-level section index for color
}>();

const { renderInline } = useKatex();

const baseUrl = import.meta.env.BASE_URL;

function renderParagraph(text: string): string {
    return text.replace(/\$([^$]+)\$/g, (_, tex) => {
        return `<span class="math-inline">${renderInline(tex)}</span>`;
    });
}

/** Block-level HTML can't be nested inside <p> tags */
function isBlockHtml(text: string): boolean {
    return /^<(ol|ul|dl|blockquote|div)\b/.test(text.trim());
}
</script>

<template>
    <PaperSection
        :id="section.id"
        :number="section.number"
        :title="section.title"
        :depth="depth"
        :section-index="sectionIndex"
    >
        <!-- Paragraphs with inline math -->
        <template v-for="(para, pi) in section.paragraphs" :key="pi">
            <div
                v-if="isBlockHtml(para)"
                :class="{ 'mt-4': pi > 0 }"
                v-html="renderParagraph(para)"
            />
            <p
                v-else
                :class="{ 'mt-4': pi > 0 }"
                v-html="renderParagraph(para)"
            />
        </template>

        <!-- Figures -->
        <template v-if="section.figures">
            <figure
                v-for="(fig, fi) in section.figures"
                :key="fi"
                class="my-6 flex flex-col items-center gap-2"
            >
                <img
                    :src="`${baseUrl}assets/${fig.filename}`"
                    :alt="fig.caption"
                    class="max-w-full rounded-lg shadow-sm"
                    :class="fig.filename.includes('portrait') ? 'paper-portrait' : 'paper-figure'"
                    style="max-height: 400px"
                    loading="lazy"
                />
                <figcaption v-if="fig.caption" class="text-sm text-muted-foreground text-center max-w-lg cm-serif italic" v-html="renderParagraph(fig.caption)" />
            </figure>
        </template>

        <!-- Theorems -->
        <template v-if="section.theorems">
            <Theorem
                v-for="(thm, ti) in section.theorems"
                :key="ti"
                :type="thm.type"
                :name="thm.name"
            >
                <p v-if="thm.body.trim()" v-html="renderParagraph(thm.body)" />
                <MathBlock
                    v-for="(eq, ei) in thm.math"
                    :key="ei"
                    :tex="eq"
                />
            </Theorem>
        </template>

        <!-- Recursive subsections -->
        <template v-if="section.subsections">
            <PaperSectionContent
                v-for="sub in section.subsections"
                :key="sub.id"
                :section="sub"
                :depth="depth + 1"
                :section-index="sectionIndex"
            />
        </template>

        <!-- Interactive callout -->
        <div v-if="section.callout" class="interactive-callout">
            <p class="cm-serif text-sm text-muted-foreground mb-3">{{ section.callout.text }}</p>
            <router-link
                :to="section.callout.link"
                class="callout-btn"
            >
                <span class="fourier-f">ℱ</span>
                <span>Open Visualizer</span>
                <ArrowRight class="h-4 w-4" />
            </router-link>
        </div>
    </PaperSection>
</template>

<style scoped>
.paper-figure {
    border: 1px solid hsl(var(--border) / 0.5);
    background: white;
    border-radius: 0.5rem;
}

/* Dark mode: invert the figure colors, then hue-rotate to fix color shifts */
:where(.dark) .paper-figure {
    filter: invert(1) hue-rotate(180deg);
    background: transparent;
    border-color: hsl(var(--border) / 0.3);
}

.paper-portrait {
    border: 1px solid hsl(var(--border) / 0.5);
    border-radius: 0.5rem;
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

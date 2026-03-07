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

function renderParagraph(text: string): string {
    return text.replace(/\$([^$]+)\$/g, (_, tex) => {
        return `<span class="math-inline">${renderInline(tex)}</span>`;
    });
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
        <p
            v-for="(para, pi) in section.paragraphs"
            :key="pi"
            :class="{ 'mt-4': pi > 0 }"
            v-html="renderParagraph(para)"
        />

        <!-- Figures -->
        <template v-if="section.figures">
            <figure
                v-for="(fig, fi) in section.figures"
                :key="fi"
                class="my-6 flex flex-col items-center gap-2"
            >
                <img
                    :src="`/assets/${fig.filename}`"
                    :alt="fig.caption"
                    class="max-w-full rounded-lg border border-border/50 shadow-sm"
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
                <p v-html="renderParagraph(thm.body)" />
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
            <p class="font-medium text-foreground mb-2">Interactive: {{ section.callout.text }}</p>
            <router-link
                :to="section.callout.link"
                class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline transition-colors"
            >
                Open in Visualize tab
                <ArrowRight class="h-3.5 w-3.5" />
            </router-link>
        </div>
    </PaperSection>
</template>

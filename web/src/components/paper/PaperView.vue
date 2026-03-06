<script setup lang="ts">
import MathBlock from "./MathBlock.vue";
import MathInline from "./MathInline.vue";
import PaperSection from "./PaperSection.vue";
import Theorem from "./Theorem.vue";
import { ArrowRight } from "lucide-vue-next";
import { paperSections } from "@/lib/paperContent";
import { computed } from "vue";
import { useKatex } from "@/composables/useKatex";

const { renderInline } = useKatex();

/** Render inline $...$ LaTeX within a plain text string to HTML */
function renderParagraph(text: string): string {
    return text.replace(/\$([^$]+)\$/g, (_, tex) => {
        return `<span class="math-inline">${renderInline(tex)}</span>`;
    });
}

const sections = computed(() => paperSections);
</script>

<template>
    <article class="paper-article mx-auto max-w-3xl px-6 py-14 leading-relaxed animate-fade-in">
        <!-- Title block -->
        <header class="mb-20 text-center">
            <h1
                class="cm-serif text-4xl font-bold tracking-tight sm:text-5xl md:text-[3.25rem] depth-text leading-[1.15]"
            >
                An Introduction to<br />Fourier Analysis
            </h1>
            <p class="mt-5 text-lg tracking-wide text-muted-foreground cm-serif" style="font-variant: small-caps;">
                From Heat Equations to Epicycles — An Interactive Companion
            </p>
        </header>

        <!-- Table of Contents -->
        <nav class="mb-14 cm-serif text-sm text-muted-foreground">
            <ol class="list-none space-y-1.5 pl-0">
                <li v-for="section in sections" :key="section.id">
                    <a :href="'#' + section.id" class="hover:text-foreground transition-colors duration-150">
                        {{ section.number }}. {{ section.title }}
                    </a>
                </li>
            </ol>
        </nav>

        <!-- Dynamic sections from paperContent.ts -->
        <PaperSection
            v-for="section in sections"
            :key="section.id"
            :id="section.id"
            :number="section.number"
            :title="section.title"
        >
            <!-- Paragraphs with inline math -->
            <p
                v-for="(para, pi) in section.paragraphs"
                :key="pi"
                :class="{ 'mt-4': pi > 0 }"
                v-html="renderParagraph(para)"
            />

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
    </article>
</template>

<style scoped>
.paper-article {
    font-feature-settings: "liga", "kern";
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    hyphens: auto;
}

/* Interactive callout cards */
.interactive-callout {
    margin: 2rem 0;
    padding: 1.25rem 1.5rem;
    border-radius: 0.75rem;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--card));
    text-align: center;
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1),
                box-shadow 0.3s cubic-bezier(0.25, 0.1, 0.25, 1),
                border-color 0.3s ease;
}

.interactive-callout:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
    border-color: hsl(var(--primary) / 0.2);
}

:deep(.dark) .interactive-callout:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}
</style>

<script setup lang="ts">
import { useKatex } from "@/composables/useKatex";

defineProps<{
    id: string;
    number: string;
    title: string;
    depth?: number; // 0 = chapter, 1 = section, 2 = subsection
    sectionIndex?: number; // top-level section index for color
}>();

const { renderInline } = useKatex();

function renderTitle(text: string): string {
    return text.replace(/\$([^$]+)\$/g, (_, tex) => {
        return `<span class="math-inline">${renderInline(tex)}</span>`;
    });
}
</script>

<template>
    <section
        :id="id"
        class="paper-section scroll-mt-20"
        :class="depth === 0 ? 'mb-14' : 'mb-8'"
        :style="(depth ?? 0) === 0 && sectionIndex != null ? `--_section-color: var(--section-color-${sectionIndex})` : ''"
    >
        <div
            class="section-header"
            :class="{
                'section-header--chapter': (depth ?? 0) === 0,
                'section-header--sub': (depth ?? 0) > 0,
            }"
        >
            <component
                :is="(depth ?? 0) > 0 ? 'h3' : 'h2'"
                class="section-heading cm-serif mb-0 font-bold tracking-normal leading-tight"
                :class="(depth ?? 0) > 0 ? 'text-[1.25rem]' : 'text-[1.625rem]'"
            >
                <span class="section-number fira-code font-normal mr-1.5 select-none"
                      :class="(depth ?? 0) > 0 ? 'text-[0.8rem]' : 'text-[0.95rem]'"
                >{{ number }}.</span>
                <span class="section-title" v-html="renderTitle(title)" />
            </component>
            <div v-if="(depth ?? 0) === 0" class="section-divider mt-4" />
        </div>
        <div class="section-body mt-5 text-base lg:text-lg leading-[1.8] text-foreground/90">
            <slot />
        </div>
    </section>
</template>

<style scoped>
/* Chapter headers (depth 0) are sticky */
.section-header--chapter {
    position: sticky;
    top: 0;
    z-index: 10;
    background: hsl(var(--card));
    box-shadow: none;
    padding: 0.75rem 1rem 0.25rem;
    margin-left: -1rem;
    margin-right: -1rem;
    border-radius: var(--radius);
}

/* Subsection headers stick below the chapter header */
.section-header--sub {
    position: sticky;
    top: 3.5rem;
    z-index: 9;
    background: hsl(var(--card));
    box-shadow: none;
    padding: 0.5rem 1rem 0.125rem;
    margin-left: -1rem;
    margin-right: -1rem;
    border-radius: var(--radius);
}

/* Chapter heading uses per-section color */
.section-header--chapter .section-heading {
    color: var(--_section-color, hsl(var(--section-heading)));
}

.section-header--chapter .section-number {
    color: color-mix(in srgb, var(--_section-color, hsl(var(--section-heading))) 50%, transparent);
}

.section-header--chapter .section-divider {
    height: 1px;
    background: linear-gradient(
        to right,
        color-mix(in srgb, var(--_section-color, hsl(var(--section-heading))) 30%, transparent),
        color-mix(in srgb, var(--_section-color, hsl(var(--section-heading))) 10%, transparent),
        transparent
    );
}

/* Subsection heading — inherit parent section color */
.section-header--sub .section-heading {
    color: var(--_section-color, hsl(var(--section-heading)));
}

.section-header--sub .section-number {
    color: color-mix(in srgb, var(--_section-color, hsl(var(--section-heading))) 50%, transparent);
}

/* Section number gets brighter on heading hover */
.section-heading:hover .section-number {
    opacity: 0.85;
    transition: opacity 0.2s ease;
}

/* Prose rhythm within sections */
.section-body :deep(p + p) {
    margin-top: 1rem;
}

.section-body :deep(em) {
    font-style: italic;
    color: hsl(var(--foreground));
}

.section-body :deep(strong) {
    font-weight: 700;
    color: hsl(var(--foreground));
}

.section-body :deep(.paper-code) {
    font-family: "Fira Code", monospace;
    font-size: 0.85em;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    background: hsl(var(--muted) / 0.5);
    color: hsl(var(--foreground));
}

.section-body :deep(.paper-cite) {
    font-style: normal;
    font-size: 0.8em;
    color: hsl(var(--primary));
    cursor: default;
    font-family: "Fira Code", monospace;
    vertical-align: super;
    line-height: 0;
}

.section-body :deep(.paper-quote) {
    border-left: 3px solid hsl(var(--border));
    margin: 1rem 0;
    padding: 0.75rem 1.25rem;
    color: hsl(var(--muted-foreground));
    font-style: italic;
    background: hsl(var(--muted) / 0.2);
    border-radius: 0 0.375rem 0.375rem 0;
}

.section-body :deep(.paper-list) {
    margin: 0.75rem 0;
    padding-left: 1.5rem;
}

.section-body :deep(.paper-list li) {
    margin: 0.25rem 0;
}

.section-body :deep(.paper-description) {
    margin: 0.75rem 0;
}

.section-body :deep(.paper-description dt) {
    font-weight: 700;
    margin-top: 0.5rem;
}

.section-body :deep(.paper-description dd) {
    margin-left: 1.5rem;
    margin-top: 0.125rem;
}
</style>

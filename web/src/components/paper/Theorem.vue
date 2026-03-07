<script setup lang="ts">
import { useKatex } from "@/composables/useKatex";

defineProps<{
    type: "theorem" | "definition" | "lemma" | "proposition" | "corollary" | "aside" | "example";
    name?: string;
}>();

const { renderInline } = useKatex();

const labels: Record<string, string> = {
    theorem: "Theorem",
    definition: "Definition",
    lemma: "Lemma",
    proposition: "Proposition",
    corollary: "Corollary",
    aside: "Aside",
    example: "Example",
};

const accentColors: Record<string, string> = {
    theorem: "border-primary",
    definition: "border-accent-pink",
    lemma: "border-muted-foreground",
    proposition: "border-primary",
    corollary: "border-primary",
    aside: "border-muted-foreground",
    example: "border-accent-pink",
};

function renderName(text: string): string {
    return text.replace(/\$([^$]+)\$/g, (_, tex) => {
        return `<span class="math-inline">${renderInline(tex)}</span>`;
    });
}
</script>

<template>
    <div
        class="theorem-block my-4 rounded-lg border-l-[3px] bg-card paper-texture px-5 py-3 transition-all duration-300"
        :class="accentColors[type]"
    >
        <p class="theorem-label mb-1 cm-serif"
           :class="{
               'text-primary': type === 'theorem' || type === 'proposition' || type === 'corollary',
               'text-[hsl(var(--accent-pink))]': type === 'definition' || type === 'example',
               'text-muted-foreground': type === 'lemma' || type === 'aside',
           }"
        >
            <span class="font-bold" style="font-variant: small-caps;">{{ labels[type] }}</span><template v-if="name"> — <em class="font-normal" v-html="renderName(name)" /></template>
        </p>
        <div class="theorem-body text-[0.938rem] leading-[1.75] text-foreground/90"
             :class="{ 'italic': type === 'theorem' || type === 'lemma' || type === 'proposition' || type === 'corollary' }"
        >
            <slot />
        </div>
    </div>
</template>

<style scoped>
.theorem-block {
    position: relative;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
    transition: box-shadow 0.3s ease, transform 0.3s ease, border-color 0.3s ease;
}

.theorem-block:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04);
    transform: translateY(-1px);
}

:where(.dark) .theorem-block {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.1);
}

:where(.dark) .theorem-block:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25), 0 2px 4px rgba(0, 0, 0, 0.15);
}

/* Faint top-right ornament for theorems */
.theorem-block::before {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 3rem;
    height: 3rem;
    border-top: 1px solid hsl(var(--border));
    border-right: 1px solid hsl(var(--border));
    border-radius: 0 0.5rem 0 0;
    opacity: 0.5;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

.theorem-block:hover::before {
    opacity: 0.8;
}

/* Tighter spacing for math blocks within theorems */
.theorem-body :deep(.math-block) {
    margin-left: 0.5rem;
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
}

/* Consecutive math blocks: no gap between them */
.theorem-body :deep(.math-block + .math-block) {
    margin-top: 0;
}
</style>

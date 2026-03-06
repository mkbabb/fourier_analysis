<script setup lang="ts">
defineProps<{
    type: "theorem" | "definition" | "lemma" | "proposition";
    name?: string;
}>();

const labels: Record<string, string> = {
    theorem: "Theorem",
    definition: "Definition",
    lemma: "Lemma",
    proposition: "Proposition",
};

const accentColors: Record<string, string> = {
    theorem: "border-primary",
    definition: "border-accent-red",
    lemma: "border-muted-foreground",
    proposition: "border-primary",
};
</script>

<template>
    <div
        class="theorem-block my-8 rounded-lg border-l-[3px] bg-card paper-texture px-6 py-5 transition-all duration-300 card-hover"
        :class="accentColors[type]"
    >
        <p class="theorem-label mb-3 cm-serif"
           :class="{
               'text-primary': type === 'theorem' || type === 'proposition',
               'text-[hsl(var(--accent-red))]': type === 'definition',
               'text-muted-foreground': type === 'lemma',
           }"
        >
            <span class="font-bold" style="font-variant: small-caps;">{{ labels[type] }}</span><template v-if="name"> — <em class="font-normal">{{ name }}</em></template>
        </p>
        <div class="theorem-body text-[0.938rem] leading-[1.75] text-foreground/90">
            <slot />
        </div>
    </div>
</template>

<style scoped>
.theorem-block {
    position: relative;
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

/* Slightly indent math blocks within theorems */
.theorem-body :deep(.math-block) {
    margin-left: 0.5rem;
}
</style>

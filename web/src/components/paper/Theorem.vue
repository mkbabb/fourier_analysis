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
</script>

<template>
    <div class="my-6 rounded-xl border-l-4 border-primary bg-card paper-texture p-5 transition-colors duration-200 card-hover">
        <p class="mb-2 text-xs font-bold uppercase tracking-widest text-primary fraunces">
            {{ labels[type] }}<template v-if="name"> — {{ name }}</template>
        </p>
        <div class="text-[0.95rem] leading-[1.7]">
            <slot />
        </div>
    </div>
</template>

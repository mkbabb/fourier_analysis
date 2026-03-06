<script setup lang="ts">
import { computed } from "vue";
import { useKatex } from "@/composables/useKatex";

const props = defineProps<{ tex: string }>();
const { renderDisplay } = useKatex();
const html = computed(() => renderDisplay(props.tex));
</script>

<template>
    <div class="math-block" v-html="html" />
</template>

<style scoped>
.math-block {
    overflow-x: auto;
    overflow-y: hidden;
    padding: 1rem 0;
    margin: 1.25rem 0;
    text-align: center;
}

/* Subtle left accent on hover — echoes theorem styling */
.math-block {
    border-left: 2px solid transparent;
    padding-left: 1rem;
    border-radius: 2px;
    transition: border-color 0.3s ease;
}

.math-block:hover {
    border-left-color: hsl(var(--border));
}
</style>

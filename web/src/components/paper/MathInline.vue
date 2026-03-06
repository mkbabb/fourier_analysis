<script setup lang="ts">
import { useKatex } from "@/composables/useKatex";

const props = defineProps<{ tex: string }>();
const { renderInline } = useKatex();
// Render once eagerly — the tex prop is static content that never changes,
// so a computed/reactive wrapper adds overhead with no benefit.
const html = renderInline(props.tex);
</script>

<template>
    <span class="math-inline" v-once v-html="html" />
</template>

<style scoped>
.math-inline {
    /* Prevent line-break inside inline math */
    white-space: nowrap;
}
</style>

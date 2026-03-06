<script setup lang="ts">
import { computed } from "vue";
import { useKatex } from "@/composables/useKatex";

const props = defineProps<{ tex: string }>();
const { renderDisplay } = useKatex();
const html = computed(() => renderDisplay(props.tex));
</script>

<template>
    <div class="katex-display my-4" v-html="html" />
</template>

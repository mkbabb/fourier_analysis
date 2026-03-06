<script setup lang="ts">
import { computed } from "vue";
import { useKatex } from "@/composables/useKatex";

const props = defineProps<{ tex: string }>();
const { renderInline } = useKatex();
const html = computed(() => renderInline(props.tex));
</script>

<template>
    <span v-html="html" />
</template>

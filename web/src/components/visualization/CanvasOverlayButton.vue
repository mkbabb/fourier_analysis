<script setup lang="ts">
defineProps<{
    active?: boolean;
}>();
</script>

<template>
    <button
        class="glass-btn"
        :class="{ 'is-active': active }"
    >
        <slot />
    </button>
</template>

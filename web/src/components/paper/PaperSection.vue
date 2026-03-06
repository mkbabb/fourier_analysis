<script setup lang="ts">
defineProps<{
    id: string;
    number: string;
    title: string;
}>();
</script>

<template>
    <section :id="id" class="mb-12 scroll-mt-20">
        <h2 class="fraunces mb-4 text-2xl font-bold tracking-tight">
            <span class="text-muted-foreground fira-code text-lg">{{ number }}.</span>
            {{ title }}
        </h2>
        <div class="text-[0.95rem] leading-[1.75] text-foreground/90">
            <slot />
        </div>
    </section>
</template>

<script setup lang="ts">
defineProps<{
    id: string;
    number: string;
    title: string;
}>();
</script>

<template>
    <section :id="id" class="paper-section mb-14 scroll-mt-20">
        <h2 class="section-heading cm-serif mb-5 text-[1.5rem] font-bold tracking-normal leading-tight">
            <span class="section-number fira-code text-[0.9rem] font-normal text-muted-foreground/70 mr-1.5 select-none">{{ number }}.</span>
            <span class="section-title">{{ title }}</span>
        </h2>
        <div class="section-divider mb-6" />
        <div class="section-body text-[0.938rem] leading-[1.8] text-foreground/90">
            <slot />
        </div>
    </section>
</template>

<style scoped>
/* Decorative divider below section heading */
.section-divider {
    height: 1px;
    background: linear-gradient(
        to right,
        hsl(var(--border)),
        hsl(var(--border) / 0.3),
        transparent
    );
}

/* Section number gets a subtle underline on heading hover */
.section-heading:hover .section-number {
    color: hsl(var(--muted-foreground));
    transition: color 0.2s ease;
}

/* Prose rhythm within sections */
.section-body :deep(p + p) {
    margin-top: 1rem;
}

.section-body :deep(em) {
    font-style: italic;
    color: hsl(var(--foreground));
}
</style>

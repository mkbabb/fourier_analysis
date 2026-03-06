<script setup lang="ts">
import { RouterView } from "vue-router";
import AppHeader from "@/components/layout/AppHeader.vue";
import SvgFilters from "@/components/decorative/SvgFilters.vue";
</script>

<template>
    <SvgFilters />
    <div class="min-h-screen flex flex-col bg-background text-foreground paper-texture">
        <AppHeader />
        <main class="flex-1">
            <RouterView v-slot="{ Component }">
                <Transition name="page" mode="out-in">
                    <component :is="Component" />
                </Transition>
            </RouterView>
        </main>
    </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
    opacity: 0;
    transform: translateY(6px);
}
.page-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
</style>

<script setup lang="ts">
import { RouterView } from "vue-router";
import AppHeader from "@/components/layout/AppHeader.vue";
import SvgFilters from "@/components/decorative/SvgFilters.vue";
</script>

<template>
    <SvgFilters />
    <div class="h-dvh flex flex-col bg-background text-foreground paper-texture overflow-hidden">
        <AppHeader />
        <main class="flex-1 min-h-0 flex flex-col">
            <RouterView />
        </main>
    </div>
</template>

<style scoped>
</style>

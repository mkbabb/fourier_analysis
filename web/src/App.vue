<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";
import { TooltipProvider } from "reka-ui";
import AppHeader from "@/components/layout/AppHeader.vue";
import SvgFilters from "@/components/decorative/SvgFilters.vue";
import ToastContainer from "@/components/ui/ToastContainer.vue";
import { resolveVizColors } from "@/lib/colors";

onMounted(() => {
    resolveVizColors();
    // Re-resolve when dark mode class changes
    const observer = new MutationObserver(() => resolveVizColors());
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class"],
    });
});
</script>

<template>
    <SvgFilters />
    <TooltipProvider :delay-duration="400" :skip-delay-duration="200">
        <div class="h-dvh flex flex-col bg-background text-foreground paper-texture overflow-hidden">
            <AppHeader />
            <main class="flex-1 min-h-0 flex flex-col overflow-y-auto">
                <RouterView />
            </main>
        </div>
    </TooltipProvider>
    <ToastContainer />
</template>

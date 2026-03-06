<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "@/stores/session";
import ImageUpload from "./ImageUpload.vue";
import ContourSettings from "./ContourSettings.vue";
import BasisCanvas from "./BasisCanvas.vue";
import BasisSelector from "./BasisSelector.vue";
import AnimationControls from "./AnimationControls.vue";
import CoefficientsPanel from "./CoefficientsPanel.vue";

const route = useRoute();
const store = useSessionStore();

onMounted(async () => {
    const slug = route.params.slug as string | undefined;
    if (slug) {
        await store.load(slug);
    } else if (!store.slug) {
        await store.create();
    }
});
</script>

<template>
    <div class="mx-auto max-w-[1400px] px-4 py-6 sm:px-6">
        <!-- Loading -->
        <div v-if="store.loading && !store.session" class="flex flex-col items-center justify-center py-24 gap-3">
            <div class="loading-spinner" />
            <p class="text-sm text-muted-foreground fira-code">Initializing session...</p>
        </div>

        <!-- Error -->
        <div
            v-if="store.error && !store.session"
            class="mx-auto max-w-md rounded-lg border border-accent-red/30 bg-accent-red/5 p-6 text-center"
        >
            <p class="text-sm text-accent-red">{{ store.error }}</p>
        </div>

        <!-- Main workspace -->
        <template v-if="store.session">
            <div class="grid grid-cols-1 gap-6 lg:grid-cols-[360px_1fr] xl:grid-cols-[400px_1fr]">
                <!-- Left panel: Controls -->
                <div class="space-y-4 animate-fade-in">
                    <ImageUpload />
                    <Transition name="slide-down">
                        <ContourSettings v-if="store.hasImage" />
                    </Transition>
                    <Transition name="slide-down">
                        <BasisSelector v-if="store.epicycleData || store.basesData" />
                    </Transition>
                    <Transition name="slide-down">
                        <CoefficientsPanel v-if="store.epicycleData" />
                    </Transition>
                </div>

                <!-- Right panel: Canvas + controls -->
                <div class="space-y-4 animate-fade-in" style="animation-delay: 0.05s">
                    <BasisCanvas />
                    <Transition name="slide-down">
                        <AnimationControls v-if="store.epicycleData" />
                    </Transition>
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.loading-spinner {
    width: 2rem;
    height: 2rem;
    border: 2.5px solid hsl(var(--border));
    border-top-color: hsl(var(--primary));
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.slide-down-enter-active {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-down-leave-active {
    transition: all 0.2s ease;
}
.slide-down-enter-from {
    opacity: 0;
    transform: translateY(-8px);
}
.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
</style>

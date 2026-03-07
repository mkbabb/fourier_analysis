<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "@/stores/session";
import { useImageUpload } from "@/composables/useImageUpload";
import { Upload } from "lucide-vue-next";
import ImageUpload from "./ImageUpload.vue";
import ContourSettings from "./ContourSettings.vue";
import BasisCanvas from "./BasisCanvas.vue";
import BasisSelector from "./BasisSelector.vue";
import AnimationControls from "./AnimationControls.vue";
import CoefficientsPanel from "./CoefficientsPanel.vue";
import ExportModal from "./ExportModal.vue";
import BouncyToggle from "@/components/ui/BouncyToggle.vue";

const route = useRoute();
const store = useSessionStore();

const { isDragging: globalDragging, handleDrop: globalDrop, handleDragOver: globalDragOver, handleDragLeave: globalDragLeave } =
    useImageUpload(async (file: File) => {
        await store.uploadImage(file);
    });

const savedBases = localStorage.getItem("fourier_active_bases");
const activeBases = ref<string[]>(
    savedBases ? JSON.parse(savedBases) : ["fourier-epicycles"],
);

const canvasComponent = ref<InstanceType<typeof BasisCanvas>>();

// Mobile tab: Controls vs Canvas
const mobileView = ref<"controls" | "canvas">("canvas");

// Export modal
const showExport = ref(false);

function handleExportFrame() {
    showExport.value = true;
}

function doExport(options: Record<string, boolean>) {
    canvasComponent.value?.exportFrame(options);
    showExport.value = false;
}

watch(activeBases, (v) => {
    localStorage.setItem("fourier_active_bases", JSON.stringify(v));
}, { deep: true });

onMounted(async () => {
    const slug = route.params.slug as string | undefined;
    if (slug) {
        await store.load(slug);
    } else if (!store.slug) {
        await store.create();
    }
});

const hasData = () => store.epicycleData || store.basesData;
const hasEpicycles = () => activeBases.value.includes("fourier-epicycles");
</script>

<template>
    <div class="viz-container"
        @drop="globalDrop"
        @dragover="globalDragOver"
        @dragleave="globalDragLeave"
    >
        <!-- Global drag overlay -->
        <Transition name="fade">
            <div v-if="globalDragging" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm pointer-events-none">
                <div class="flex flex-col items-center gap-3 text-muted-foreground">
                    <Upload class="h-12 w-12" />
                    <p class="text-lg font-medium">Drop image anywhere</p>
                </div>
            </div>
        </Transition>

        <!-- Loading -->
        <div v-if="store.loading && !store.session" class="flex flex-col items-center justify-center flex-1 gap-3">
            <div class="loading-spinner" />
            <p class="text-sm text-muted-foreground fira-code">Initializing session...</p>
        </div>

        <!-- Error -->
        <div
            v-else-if="store.error && !store.session"
            class="flex items-center justify-center flex-1"
        >
            <div class="mx-auto max-w-md cartoon-card p-6 text-center">
                <p class="text-sm text-accent-red">{{ store.error }}</p>
            </div>
        </div>

        <!-- Main workspace -->
        <div v-else-if="store.session" class="viz-workspace">
            <!-- Mobile tab bar -->
            <div class="mobile-tab-bar">
                <BouncyToggle
                    class="w-full"
                    :options="[
                        { label: 'Controls', value: 'controls' },
                        { label: 'Canvas', value: 'canvas' },
                    ]"
                    :model-value="mobileView"
                    @update:model-value="mobileView = $event as 'controls' | 'canvas'"
                />
            </div>

            <div class="viz-grid">
                <!-- Left panel: Controls -->
                <div class="viz-panel-left-wrap" :class="{ 'mobile-hidden': mobileView !== 'controls' }">
                    <div class="viz-panel-left">
                        <ImageUpload />
                        <Transition name="slide-down">
                            <ContourSettings v-if="store.hasImage" />
                        </Transition>
                        <Transition name="slide-down">
                            <BasisSelector
                                v-if="hasData()"
                                :active-bases="activeBases"
                                @update:active-bases="activeBases = $event"
                            />
                        </Transition>
                        <Transition name="slide-down">
                            <CoefficientsPanel v-if="store.epicycleData" />
                        </Transition>
                    </div>
                </div>

                <!-- Right panel: Canvas + transport -->
                <div class="viz-panel-right" :class="{ 'mobile-hidden': mobileView !== 'canvas' }">
                    <BasisCanvas ref="canvasComponent" :active-bases="activeBases" />
                    <AnimationControls
                        v-if="hasData()"
                        :active-bases="activeBases"
                        @export-frame="handleExportFrame"
                    />
                </div>
            </div>
        </div>

        <!-- Export modal -->
        <ExportModal
            v-if="showExport"
            :has-epicycles="hasEpicycles()"
            @export="doExport"
            @close="showExport = false"
        />
    </div>
</template>

<style scoped>
.viz-container {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

.viz-workspace {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

.viz-grid {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    padding: 0.75rem;
    gap: 0.75rem;
}

@media (min-width: 1024px) {
    .viz-grid {
        display: grid;
        grid-template-columns: 340px 1fr;
        gap: 1rem;
        padding: 1rem;
        padding-bottom: 1.5rem;
    }
}

@media (min-width: 1280px) {
    .viz-grid {
        grid-template-columns: 380px 1fr;
    }
}

@media (min-width: 1536px) {
    .viz-grid {
        grid-template-columns: 420px 1fr;
    }
}

.viz-panel-left-wrap {
    position: relative;
    display: flex;
    flex-direction: column;
    max-width: 480px;
    margin: 0 auto;
    width: 100%;
    min-height: 0;
    overflow: hidden;
    flex: 1;
}

/* Bottom fade overlay */
.viz-panel-left-wrap::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2.5rem;
    background: linear-gradient(to bottom, transparent, hsl(var(--background)));
    pointer-events: none;
    z-index: 2;
}

@media (min-width: 1024px) {
    .viz-panel-left-wrap {
        max-width: none;
        margin: 0;
    }
}

.viz-panel-left {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: 100%;
    padding-bottom: 2rem;
    overflow-y: auto;
    min-height: 0;
    flex: 1;
}

@media (min-width: 1024px) {
    .viz-panel-left {
        padding-right: 0.25rem;
    }
}

.viz-panel-right {
    display: flex;
    flex-direction: column;
    gap: 0;
    min-height: 0;
    overflow: hidden;
    flex: 1;
}


/* ── Mobile tab bar ── */
.mobile-tab-bar {
    display: flex;
    justify-content: center;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--background));
}

@media (min-width: 1024px) {
    .mobile-tab-bar {
        display: none;
    }
}

/* Hide inactive panel on mobile only */
@media (max-width: 1023px) {
    .mobile-hidden {
        display: none;
    }
}

/* ── Shared ──────────────────────────────────── */
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
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>

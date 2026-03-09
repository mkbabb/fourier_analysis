<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSessionStore } from "@/stores/session";
import { useImageUpload } from "./composables/useImageUpload";
import { Upload, AlertTriangle, X } from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";
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

const { isDragging: globalDragging, handleDrop: globalDrop, handleDragOver: globalDragOver, handleDragEnter: globalDragEnter, handleDragLeave: globalDragLeave } =
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
        // If load failed (stale/invalid slug), create a fresh session
        if (!store.session && store.error) {
            store.error = null;
            await store.create();
        }
    } else if (!store.slug) {
        await store.create();
    }
});

// Shared N/points state — lifted so both ContourSettings and BasisSelector can bind
const nHarmonics = ref(store.session?.parameters?.n_harmonics ?? 200);
const nPoints = ref(store.session?.parameters?.n_points ?? 1024);

// Seed from session once it loads (e.g. after store.load())
if (!store.session) {
    watch(() => store.session, (s) => {
        if (s?.parameters) {
            nHarmonics.value = s.parameters.n_harmonics ?? 200;
            nPoints.value = s.parameters.n_points ?? 1024;
        }
    }, { once: true });
}

// Reset harmonics to 1 on new image upload to avoid flash from high N
watch(() => store.hasImage, (has, prevHas) => {
    if (has && !prevHas) {
        nHarmonics.value = 1;
    }
});

const hasData = computed(() => store.epicycleData || store.basesData);
const hasEpicycles = computed(() => activeBases.value.includes("fourier-epicycles"));

const showGhost = ref(true);
watch(showGhost, (v) => {
    if (canvasComponent.value) canvasComponent.value.showGhost = v;
});

function dismissError() {
    store.error = null;
}
</script>

<template>
    <div class="viz-container"
        @drop="globalDrop"
        @dragover="globalDragOver"
        @dragenter="globalDragEnter"
        @dragleave="globalDragLeave"
    >
        <!-- Global drag overlay -->
        <Transition name="fade">
            <div v-if="globalDragging" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
                @drop="globalDrop" @dragover.prevent>
                <div class="flex flex-col items-center gap-3 text-muted-foreground">
                    <Upload class="h-12 w-12" />
                    <p class="text-lg font-medium">Drop image anywhere</p>
                </div>
            </div>
        </Transition>

        <!-- Loading -->
        <div v-if="store.loading && !store.session" class="flex flex-col items-center justify-center flex-1 gap-3">
            <div class="h-8 w-8 animate-spin rounded-full border-[2.5px] border-border border-t-primary" />
            <p class="text-sm text-muted-foreground fira-code">Initializing session...</p>
        </div>

        <!-- Error (no session) -->
        <div
            v-else-if="store.error && !store.session"
            class="flex items-center justify-center flex-1"
        >
            <div class="mx-auto max-w-md cartoon-card p-6 text-center space-y-3">
                <AlertTriangle class="h-8 w-8 text-amber-500 mx-auto" />
                <p class="text-sm font-medium text-foreground">Could not connect to the server</p>
                <p class="text-xs text-muted-foreground fira-code break-all">{{ store.error }}</p>
                <Tooltip text="Try connecting to the server again">
                    <button
                        class="mt-2 px-4 py-2 text-sm font-medium rounded-lg border-2 border-foreground/15 bg-background hover:bg-muted transition-colors cursor-pointer"
                        @click="store.create()"
                    >
                        Retry
                    </button>
                </Tooltip>
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

            <!-- Inline error banner -->
            <Transition name="slide-down">
                <div v-if="store.error && store.session" class="error-banner">
                    <AlertTriangle class="h-4 w-4 text-amber-500 flex-shrink-0" />
                    <p class="flex-1 text-xs fira-code truncate">{{ store.error }}</p>
                    <Tooltip text="Dismiss error">
                        <button class="flex-shrink-0 p-0.5 rounded hover:bg-foreground/10 cursor-pointer" @click="dismissError">
                            <X class="h-3.5 w-3.5" />
                        </button>
                    </Tooltip>
                </div>
            </Transition>

            <div class="viz-grid">
                <!-- Left panel: Controls -->
                <div class="viz-panel-left-wrap" :class="{ 'mobile-hidden': mobileView !== 'controls' }">
                    <div class="viz-panel-left">
                        <ImageUpload />
                        <Transition name="slide-down">
                            <ContourSettings v-if="store.hasImage"
                                v-model:n-harmonics="nHarmonics"
                                v-model:n-points="nPoints"
                            />
                        </Transition>
                        <Transition name="slide-down">
                            <BasisSelector
                                v-if="hasData"
                                :active-bases="activeBases"
                                v-model:n-harmonics="nHarmonics"
                                v-model:n-points="nPoints"
                                @update:active-bases="activeBases = $event"
                            />
                        </Transition>
                        <Transition name="slide-down">
                            <CoefficientsPanel v-if="store.epicycleData" />
                        </Transition>
                    </div>
                </div>

                <!-- Right panel: Canvas with overlaid controls -->
                <div class="viz-panel-right" :class="{ 'mobile-hidden': mobileView !== 'canvas' }">
                    <BasisCanvas ref="canvasComponent" :active-bases="activeBases" />
                    <div v-if="hasData" class="controls-overlay">
                        <AnimationControls
                            :active-bases="activeBases"
                            :show-ghost="showGhost"
                            @export-frame="handleExportFrame"
                            @toggle-ghost="showGhost = !showGhost"
                        />
                    </div>
                </div>
            </div>
        </div>

        <!-- Export modal -->
        <ExportModal
            v-if="showExport"
            :has-epicycles="hasEpicycles"
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
        grid-template-columns: 360px 1fr;
        grid-template-rows: 1fr;
        gap: 0.75rem;
        padding: 0.75rem;
        padding-bottom: 1.25rem;
        overflow: hidden;
    }
}

@media (min-width: 1280px) {
    .viz-grid {
        grid-template-columns: 400px 1fr;
    }
}

@media (min-width: 1536px) {
    .viz-grid {
        grid-template-columns: 440px 1fr;
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
    min-width: 0;
    overflow: hidden;
    flex: 1;
    position: relative;
}

/* Controls overlaid at bottom of canvas — floats over grid */
.controls-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 20;
    border-radius: 0 0 0.75rem 0.75rem;
    overflow: visible;
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

/* ── Error banner ── */
.error-banner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.5rem 0.75rem 0;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    background: hsl(var(--destructive) / 0.08);
    border: 1.5px solid hsl(var(--destructive) / 0.2);
    color: hsl(var(--foreground));
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

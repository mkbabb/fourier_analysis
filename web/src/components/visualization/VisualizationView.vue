<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { watchDebounced, useMediaQuery } from "@vueuse/core";
import { useRouter } from "vue-router";
import { useWorkspaceStore } from "@/stores/workspace";
import { useAnimationStore } from "@/stores/animation";
import { useImageUpload } from "./composables/useImageUpload";
import { useViewState } from "./composables/useViewState";
import { useWorkspaceLoader } from "./composables/useWorkspaceLoader";
import { Upload } from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";
import { useGalleryStore } from "@/stores/gallery";
import { useToast } from "@/composables/useToast";
import ImageUpload from "./ImageUpload.vue";
import ContourSettings from "./ContourSettings.vue";
import BasisCanvas from "./BasisCanvas.vue";
import BasisSelector from "./BasisSelector.vue";
import AnimationControls from "./AnimationControls.vue";
import ContourEditorCanvas from "./ContourEditorCanvas.vue";
import EditorControlsDock from "./EditorControlsDock.vue";
import EditorToolsPanel from "./EditorToolsPanel.vue";
import ContourPreview from "./ContourPreview.vue";
import CanvasControlsDock from "./CanvasControlsDock.vue";
import CoefficientsPanel from "./CoefficientsPanel.vue";
import ExportModal from "./ExportModal.vue";
import FullscreenViewer from "./FullscreenViewer.vue";
import EquationPanel from "./EquationPanel.vue";
import UnderlineTabs from "@/components/ui/UnderlineTabs.vue";

const router = useRouter();
const store = useWorkspaceStore();
const anim = useAnimationStore();
const gallery = useGalleryStore();
const { toast } = useToast();

// ── View state (editing, ghost, overlay — persisted to localStorage) ──
const { isEditing, showGhost, showImageOverlay, showEquation } = useViewState();

// ── Image drag-and-drop ──
const { isDragging: globalDragging, handleDrop: globalDrop, handleDragOver: globalDragOver, handleDragEnter: globalDragEnter, handleDragLeave: globalDragLeave } =
    useImageUpload(async (file: File) => { await store.uploadImage(file); });

// ── Active bases ──
const activeBases = ref<string[]>(
    store.animationSettings?.active_bases ?? ["fourier-epicycles"],
);

// ── Workspace loading, contour settings, auto-play ──
const { nHarmonics, nPoints } = useWorkspaceLoader(activeBases);

// ── Persist animation settings to workspace on change ──
watchDebounced(
    () => [activeBases.value, anim.easing, anim.speed] as const,
    () => {
        if (!store.imageSlug) return;
        store.animationSettings = {
            ...store.animationSettings,
            active_bases: [...activeBases.value],
            easing: anim.easing,
            speed: anim.speed,
        };
    },
    { debounce: 500, deep: true },
);

// ── Canvas + modals ──
const canvasComponent = ref<InstanceType<typeof BasisCanvas>>();
const mobileView = ref<"controls" | "canvas">("canvas");
const isDesktop = useMediaQuery("(min-width: 1024px)");
const showExport = ref(false);
const showFullscreen = ref(false);

// ── Editor state ──
const editorState = ref({ canUndo: false, canRedo: false, canDelete: false, pointCount: 0 });
const editorRef = ref<InstanceType<typeof ContourEditorCanvas> | null>(null);
const editorSaved = ref(false);
const magnetRadius = computed({
    get: () => editorRef.value?.magnetRadius ?? 0,
    set: (v: number) => { if (editorRef.value) editorRef.value.magnetRadius = v; },
});

function onEditorStateChange(state: typeof editorState.value) {
    editorState.value = state;
    editorSaved.value = false;
}

async function onEditorSave() {
    if (!editorRef.value) return;
    await store.saveContourPoints(editorRef.value.getPoints());
    editorSaved.value = true;
}

function handleExportFrame() { showExport.value = true; }
function doExport(options: Record<string, boolean>) {
    canvasComponent.value?.exportFrame(options);
    showExport.value = false;
}

// ── Publish to gallery ──
const publishing = ref(false);
async function handlePublish() {
    if (!store.imageSlug || !store.contour) return;
    publishing.value = true;
    try {
        const snapshot = await store.createSnapshot();
        if (!snapshot) { toast("Could not create snapshot", "error"); return; }
        await gallery.publish(snapshot.snapshot_hash, store.imageSlug);
    } catch (e: any) {
        toast(e.message ?? "Publish failed", "error");
    } finally {
        publishing.value = false;
    }
}

// ── Derived state ──
const hasData = computed(() => store.epicycleData || store.basesData || store.computing);
const hasEpicycles = computed(() => activeBases.value.includes("fourier-epicycles"));
const hasImage = computed(() => !!store.imageMeta);
</script>

<template>
    <div class="flex flex-col flex-1 min-h-0"
        @drop="globalDrop" @dragover="globalDragOver"
        @dragenter="globalDragEnter" @dragleave="globalDragLeave"
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
        <div v-if="store.loading && !store.imageSlug" class="flex flex-col items-center justify-center flex-1 gap-3">
            <div class="h-8 w-8 animate-spin rounded-full border-[2.5px] border-border border-t-primary" />
            <p class="text-sm text-muted-foreground fira-code">Loading workspace...</p>
        </div>

        <!-- Error (no workspace) -->
        <div v-else-if="store.error && !store.imageSlug" class="flex items-center justify-center flex-1">
            <div class="mx-auto max-w-md cartoon-card p-6 text-center space-y-3">
                <p class="text-sm font-medium text-foreground">Could not load workspace</p>
                <p class="text-xs text-muted-foreground fira-code break-all">{{ store.error }}</p>
                <Tooltip text="Go back to upload a new image">
                    <button class="mt-2 px-4 py-2 text-sm font-medium rounded-lg border-2 border-foreground/15 bg-background hover:bg-muted transition-colors cursor-pointer"
                        @click="store.reset(); router.push('/visualize')">
                        Start fresh
                    </button>
                </Tooltip>
            </div>
        </div>

        <!-- Main workspace -->
        <div v-else class="flex flex-col flex-1 min-h-0">
            <!-- Mobile tab bar -->
            <div class="flex px-3 py-1 bg-background lg:hidden">
                <UnderlineTabs
                    :options="[{ label: 'Controls', value: 'controls' }, { label: 'Canvas', value: 'canvas' }]"
                    :model-value="mobileView"
                    @update:model-value="mobileView = $event as 'controls' | 'canvas'" />
            </div>

            <div class="viz-grid">
                <!-- Left panel: Controls -->
                <div class="viz-panel-left-wrap" :class="{ 'panel-inactive': mobileView !== 'controls' && !isDesktop }">
                    <Transition name="panel-swap" mode="out-in">
                        <div v-if="isEditing" key="editor-panel" class="viz-panel-left">
                            <!-- Preview above tools -->
                            <ContourPreview :points="editorRef?.points" />
                            <!-- Editor tools card -->
                            <EditorToolsPanel
                                :magnet-radius="magnetRadius"
                                @smooth="editorRef?.applySmooth()"
                                @simplify="editorRef?.applySimplify()"
                                @update:magnet-radius="magnetRadius = $event"
                            />
                            <ContourSettings v-if="hasImage" v-model:n-harmonics="nHarmonics" v-model:n-points="nPoints" />
                        </div>
                        <div v-else key="viz-panel" class="viz-panel-left">
                            <ImageUpload />
                            <Transition name="slide-down">
                                <BasisSelector v-if="hasData" :active-bases="activeBases"
                                    v-model:n-harmonics="nHarmonics" v-model:n-points="nPoints"
                                    @update:active-bases="activeBases = $event" />
                            </Transition>
                            <Transition name="slide-down">
                                <ContourSettings v-if="hasImage" v-model:n-harmonics="nHarmonics" v-model:n-points="nPoints" />
                            </Transition>
                            <Transition name="slide-down">
                                <CoefficientsPanel v-if="store.epicycleData || store.computing" />
                            </Transition>
                        </div>
                    </Transition>
                </div>

                <!-- Right panel: Canvas with overlaid controls -->
                <div class="viz-panel-right canvas-stage" :class="{ 'panel-inactive': mobileView !== 'canvas' && !isDesktop }">
                    <div class="canvas-container" :class="{ 'is-hidden': isEditing && store.contour }">
                        <BasisCanvas ref="canvasComponent" :active-bases="activeBases"
                            :show-ghost="showGhost" :show-image-overlay="showImageOverlay" />
                    </div>
                    <div v-if="store.contour" class="editor-shell" :class="{ 'is-hidden': !isEditing }">
                        <ContourEditorCanvas ref="editorRef" :contour="store.contour"
                            :image-slug="store.imageSlug" :show-image-overlay="showImageOverlay"
                            @state-change="onEditorStateChange" />
                    </div>

                    <!-- Top-right controls dock -->
                    <div v-if="hasData || (isEditing && store.contour)" class="absolute top-2 right-2 z-20">
                        <CanvasControlsDock
                            :is-editing="isEditing"
                            :show-image-overlay="showImageOverlay"
                            :show-ghost="showGhost"
                            :show-equation="showEquation"
                            :has-data="!!hasData"
                            :has-contour="!!store.contour"
                            :publishing="publishing"
                            @toggle-edit="isEditing = !isEditing"
                            @toggle-fullscreen="showFullscreen = true"
                            @toggle-equation="showEquation = !showEquation"
                            @toggle-image-overlay="showImageOverlay = !showImageOverlay"
                            @toggle-ghost="showGhost = !showGhost"
                            @publish="handlePublish"
                        />
                    </div>

                    <!-- Equation overlay panel -->
                    <Transition name="fade">
                        <EquationPanel v-if="showEquation && store.epicycleData && !isEditing" @close="showEquation = false" />
                    </Transition>

                    <!-- Bottom dock -->
                    <div v-if="hasData && !isEditing" class="controls-overlay">
                        <AnimationControls :active-bases="activeBases" @export-frame="handleExportFrame" />
                    </div>
                    <div v-if="isEditing && store.contour" class="controls-overlay">
                        <EditorControlsDock :can-undo="editorState.canUndo" :can-redo="editorState.canRedo"
                            :can-delete="editorState.canDelete" :point-count="editorState.pointCount"
                            :show-image-overlay="showImageOverlay" :show-ghost="showGhost"
                            :magnet-radius="magnetRadius" :is-saved="editorSaved"
                            @undo="editorRef?.undo()" @redo="editorRef?.redo()" @smooth="editorRef?.applySmooth()"
                            @simplify="editorRef?.applySimplify()" @delete="editorRef?.deleteSelected()"
                            @toggle-overlay="showImageOverlay = !showImageOverlay" @toggle-ghost="showGhost = !showGhost"
                            @update:magnet-radius="magnetRadius = $event"
                            @reset="editorRef?.resetToExtraction()" @save="onEditorSave" />
                    </div>
                </div>
            </div>
        </div>

        <ExportModal v-if="showExport" :has-epicycles="hasEpicycles" @export="doExport" @close="showExport = false" />
        <FullscreenViewer :visible="showFullscreen" :active-bases="activeBases" :show-ghost="showGhost"
            :show-image-overlay="showImageOverlay" :is-editing="isEditing" :contour="store.contour ?? undefined"
            :image-slug="store.imageSlug" @close="showFullscreen = false"
            @toggle-ghost="showGhost = !showGhost" @toggle-image-overlay="showImageOverlay = !showImageOverlay" />
    </div>
</template>

<style scoped>
/* ── Grid layout ── */
.viz-grid {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    padding: 0.25rem;
    gap: 0.25rem;
}

@media (min-width: 1024px) {
    .viz-grid {
        display: grid;
        grid-template-columns: 360px 1fr;
        grid-template-rows: 1fr;
        gap: 0.5rem;
        padding: 0.5rem;
        padding-bottom: 0.75rem;
        overflow: hidden;
    }
}
@media (min-width: 1280px) { .viz-grid { grid-template-columns: 400px 1fr; } }
@media (min-width: 1536px) { .viz-grid { grid-template-columns: 440px 1fr; } }

/* ── Left panel ── */
.viz-panel-left-wrap {
    position: relative;
    display: flex;
    flex-direction: column;
    max-width: 480px;
    margin: 0 auto;
    width: 100%;
    min-height: 0;
    overflow-x: visible;
    overflow-y: clip;
    flex: 1;
}
@media (max-width: 1023px) { .viz-panel-left-wrap { overflow: visible; flex: none; } }
@media (min-width: 1024px) { .viz-panel-left-wrap { max-width: none; margin: 0; } }

.viz-panel-left-wrap::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2.5rem;
    background: linear-gradient(to bottom, transparent, hsl(var(--background)));
    pointer-events: none;
    z-index: 2;
}
@media (max-width: 1023px) { .viz-panel-left-wrap::after { display: none; } }

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
@media (min-width: 1024px) { .viz-panel-left { padding-right: 0.25rem; } }

/* ── Right panel ── */
.viz-panel-right {
    display: flex;
    flex-direction: column;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
    flex: 1;
    position: relative;
}

/* ── Canvas crossfade ── */
/* Both canvases are always absolutely positioned so switching between them
   is a pure opacity crossfade with no layout shift. */
.canvas-stage > .canvas-container,
.canvas-stage > .editor-shell {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    min-height: 0;
    opacity: 1;
    z-index: 1;
    pointer-events: auto;
    transition: opacity var(--duration-mid, 0.24s) ease;
}
.canvas-stage > .canvas-container.is-hidden,
.canvas-stage > .editor-shell.is-hidden {
    opacity: 0;
    z-index: 0;
    pointer-events: none;
}

/* ── Controls overlay ── */
.controls-overlay {
    position: absolute;
    bottom: 0.75rem;
    left: 0.375rem;
    right: 0.375rem;
    z-index: 20;
    display: flex;
    justify-content: center;
    pointer-events: none;
    overflow: visible;
}
.controls-overlay > * { pointer-events: auto; }

/* ── Transitions ── */
.expand-pop-enter-active { transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.expand-pop-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.expand-pop-enter-from, .expand-pop-leave-to { opacity: 0; transform: scale(0.3); }

.panel-swap-enter-active, .panel-swap-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.panel-swap-enter-from { opacity: 0; transform: translateY(4px); }
.panel-swap-leave-to { opacity: 0; transform: translateY(-4px); }

.slide-down-enter-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from { opacity: 0; transform: translateY(-8px); }
.slide-down-leave-to { opacity: 0; transform: translateY(-4px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Mobile panel toggle ── */
@media (max-width: 1023px) {
    .panel-inactive {
        display: none;
    }
}

/* ── Mobile ── */
@media (max-width: 900px) {
    .viz-grid { display: flex; flex-direction: column; gap: 0.5rem; min-height: 0; }
    .controls-overlay { left: 0.5rem; right: 0.5rem; bottom: 0.75rem; }
}
</style>

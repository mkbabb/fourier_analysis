import { defineStore } from "pinia";
import { ref, watch, toRaw } from "vue";
import { useRouter } from "vue-router";
import type {
    ImageMeta,
    ContourAsset,
    EpicycleData,
    AnimationData,
    ContourSettings,
    AnimationSettings,
    WorkspaceDraft,
    Snapshot,
} from "@/lib/types";
import * as api from "@/lib/api";
import { saveDraft, loadDraft, listDrafts } from "@/lib/draftStorage";

function defaultContourSettings(): ContourSettings {
    return {
        strategy: "auto",
        resize: 800,
        blur_sigma: 2.0,
        n_harmonics: 100,
        n_points: 1024,
        n_classes: 3,
        min_contour_length: 40,
        min_contour_area: 0.01,
        max_contours: 5,
        smooth_contours: 0.1,
    };
}

function defaultAnimationSettings(): AnimationSettings {
    return {
        fps: 60,
        duration: 5000,
        max_circles: 100,
        easing: "sine",
        speed: 1,
        active_bases: ["fourier"],
    };
}

export const useWorkspaceStore = defineStore("workspace", () => {
    const router = useRouter();

    // State
    const imageSlug = ref<string | null>(null);
    const imageMeta = ref<ImageMeta | null>(null);
    const contour = ref<ContourAsset | null>(null);
    const epicycleData = ref<EpicycleData | null>(null);
    const basesData = ref<AnimationData | null>(null);
    const contourSettings = ref<ContourSettings>(defaultContourSettings());
    const animationSettings = ref<AnimationSettings>(defaultAnimationSettings());
    const drafts = ref<WorkspaceDraft[]>([]);
    const loading = ref(false);
    const computing = ref(false);
    const error = ref<string | null>(null);
    const revision = ref(0);

    // Draft auto-save (debounced)
    let draftTimer: ReturnType<typeof setTimeout> | null = null;

    function scheduleDraftSave() {
        if (!imageSlug.value) return;
        if (draftTimer) clearTimeout(draftTimer);
        draftTimer = setTimeout(() => {
            _saveDraftNow();
        }, 1000);
    }

    async function _saveDraftNow() {
        if (!imageSlug.value) return;
        // Use toRaw + JSON round-trip to strip Vue reactive proxies —
        // IndexedDB's structured clone algorithm can't handle Proxy objects.
        const raw = JSON.parse(JSON.stringify({
            imageSlug: imageSlug.value,
            contour: toRaw(contour.value),
            contourSettings: toRaw(contourSettings.value),
            animationSettings: toRaw(animationSettings.value),
            epicycleData: toRaw(epicycleData.value),
            basesData: toRaw(basesData.value),
            savedSnapshots: [],
            lastOpenedAt: new Date().toISOString(),
        })) as WorkspaceDraft;
        await saveDraft(raw).catch((e) => { console.warn("[draft] save failed:", e); });
    }

    watch([contourSettings, animationSettings], scheduleDraftSave, { deep: true });

    // Methods
    async function uploadImage(file: File) {
        loading.value = true;
        error.value = null;
        try {
            const meta = await api.uploadImage(file);
            imageSlug.value = meta.image_slug;
            imageMeta.value = meta;
            contour.value = null;
            epicycleData.value = null;
            basesData.value = null;
            router.push(`/w/${meta.image_slug}`);
            await _saveDraftNow();
        } catch (e: any) {
            if (!api.isAbortError(e)) error.value = e.message ?? "Upload failed";
            throw e;
        } finally {
            loading.value = false;
        }
    }

    async function loadWorkspace(slug: string) {
        loading.value = true;
        error.value = null;
        const rev = ++revision.value;
        try {
            const [meta, draft] = await Promise.all([
                api.getImageMeta(slug),
                loadDraft(slug),
            ]);
            if (revision.value !== rev) return;
            imageSlug.value = slug;
            imageMeta.value = meta;
            if (draft) {
                contour.value = draft.contour;
                contourSettings.value = {
                    ...defaultContourSettings(),
                    ...draft.contourSettings,
                };
                animationSettings.value = {
                    ...defaultAnimationSettings(),
                    ...draft.animationSettings,
                };
                epicycleData.value = draft.epicycleData;
                basesData.value = draft.basesData;
            } else {
                contour.value = null;
                contourSettings.value = defaultContourSettings();
                animationSettings.value = defaultAnimationSettings();
                epicycleData.value = null;
                basesData.value = null;
            }
            // Save draft immediately so gallery shows this workspace
            await _saveDraftNow();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Failed to load workspace";
            throw e;
        } finally {
            loading.value = false;
        }
    }

    async function loadSnapshot(slug: string, snapshotHash: string) {
        loading.value = true;
        error.value = null;
        const rev = ++revision.value;
        try {
            const [meta, snapshot] = await Promise.all([
                api.getImageMeta(slug),
                api.getSnapshot(slug, snapshotHash),
            ]);
            if (revision.value !== rev) return;
            imageSlug.value = slug;
            imageMeta.value = meta;
            contourSettings.value = {
                ...defaultContourSettings(),
                ...snapshot.contour_settings,
            };
            animationSettings.value = {
                ...defaultAnimationSettings(),
                ...snapshot.animation_settings,
            };
            // Load contour from snapshot
            const contourAsset = await api.getContour(snapshot.contour_hash);
            if (revision.value !== rev) return;
            contour.value = contourAsset;
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Failed to load snapshot";
            throw e;
        } finally {
            loading.value = false;
        }
    }

    async function extractContour() {
        if (!imageSlug.value) return;
        computing.value = true;
        error.value = null;
        const rev = ++revision.value;
        try {
            const result = await api.extractContour(
                imageSlug.value,
                contourSettings.value,
            );
            if (revision.value !== rev) return;
            contour.value = result;
            epicycleData.value = null;
            basesData.value = null;
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Contour extraction failed";
            throw e;
        } finally {
            computing.value = false;
        }
    }

    async function saveContourPoints(points: { x: number[]; y: number[] }) {
        if (!imageSlug.value) return;
        computing.value = true;
        error.value = null;
        try {
            const result = await api.saveContour(imageSlug.value, points);
            contour.value = result;
            epicycleData.value = null;
            basesData.value = null;
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Failed to save contour";
            throw e;
        } finally {
            computing.value = false;
        }
    }

    async function runComputeEpicycles() {
        if (!contour.value) return;
        computing.value = true;
        error.value = null;
        const rev = ++revision.value;
        try {
            const result = await api.computeEpicycles(
                contour.value.contour_hash,
                {
                    n_harmonics: contourSettings.value.n_harmonics,
                    n_points: contourSettings.value.n_points,
                },
            );
            if (revision.value !== rev) return;
            epicycleData.value = result;
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Epicycle computation failed";
            throw e;
        } finally {
            computing.value = false;
        }
    }

    async function runComputeBases() {
        if (!contour.value) return;
        computing.value = true;
        error.value = null;
        const rev = ++revision.value;
        try {
            const result = await api.computeBases(
                contour.value.contour_hash,
                {
                    max_degree: contourSettings.value.n_harmonics,
                    n_points: contourSettings.value.n_points,
                    levels: Array.from({ length: Math.min(contourSettings.value.n_harmonics, 50) }, (_, i) =>
                        Math.max(1, Math.round((i + 1) * contourSettings.value.n_harmonics / Math.min(contourSettings.value.n_harmonics, 50)))
                    ),
                    n_eval: contourSettings.value.n_points,
                },
            );
            if (revision.value !== rev) return;
            basesData.value = result;
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Bases computation failed";
            throw e;
        } finally {
            computing.value = false;
        }
    }

    async function createSnapshot(): Promise<Snapshot | null> {
        if (!imageSlug.value || !contour.value) return null;
        try {
            return await api.saveSnapshot(imageSlug.value, {
                contour_hash: contour.value.contour_hash,
                contour_settings: contourSettings.value,
                animation_settings: animationSettings.value,
            });
        } catch (e: any) {
            error.value = e.message ?? "Failed to save snapshot";
            return null;
        }
    }

    async function refreshDrafts() {
        drafts.value = await listDrafts().catch(() => []);
    }

    function reset() {
        imageSlug.value = null;
        imageMeta.value = null;
        contour.value = null;
        epicycleData.value = null;
        basesData.value = null;
        contourSettings.value = defaultContourSettings();
        animationSettings.value = defaultAnimationSettings();
        error.value = null;
        loading.value = false;
        computing.value = false;
    }

    return {
        // State
        imageSlug,
        imageMeta,
        contour,
        epicycleData,
        basesData,
        contourSettings,
        animationSettings,
        drafts,
        loading,
        computing,
        error,
        revision,
        // Methods
        uploadImage,
        loadWorkspace,
        loadSnapshot,
        extractContour,
        saveContourPoints,
        computeEpicycles: runComputeEpicycles,
        computeBases: runComputeBases,
        createSnapshot,
        refreshDrafts,
        reset,
        defaultContourSettings,
        defaultAnimationSettings,
    };
});

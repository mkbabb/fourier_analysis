import { defineStore } from "pinia";
import { ref, shallowRef, watch, toRaw, markRaw, onScopeDispose } from "vue";
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
import { defaultContourSettings, defaultAnimationSettings } from "@/lib/defaults";

export const useWorkspaceStore = defineStore("workspace", () => {
    const router = useRouter();

    // State
    const imageSlug = ref<string | null>(null);
    const imageMeta = ref<ImageMeta | null>(null);
    const contour = shallowRef<ContourAsset | null>(null);
    const epicycleData = shallowRef<EpicycleData | null>(null);
    const basesData = shallowRef<AnimationData | null>(null);
    const contourSettings = ref<ContourSettings>(defaultContourSettings());
    const animationSettings = ref<AnimationSettings>(defaultAnimationSettings());
    const drafts = ref<WorkspaceDraft[]>([]);
    const loading = ref(false);
    const computing = ref(false);
    const error = ref<string | null>(null);
    const revision = ref(0);
    // Separate revision counters for compute methods so that
    // loadWorkspace incrementing `revision` doesn't cause compute
    // results to be silently discarded, which triggers an infinite
    // retry loop in the auto-compute watcher.
    let epicycleRevision = 0;
    let basesRevision = 0;

    // Depth counter so `computing` stays true across sequential async steps
    let _computeDepth = 0;
    function beginCompute() {
        _computeDepth++;
        computing.value = true;
    }
    function endCompute() {
        _computeDepth = Math.max(0, _computeDepth - 1);
        computing.value = _computeDepth > 0;
    }

    // Draft auto-save (debounced)
    let draftTimer: ReturnType<typeof setTimeout> | null = null;

    onScopeDispose(() => {
        if (draftTimer) clearTimeout(draftTimer);
    });

    function scheduleDraftSave() {
        if (!imageSlug.value) return;
        if (draftTimer) clearTimeout(draftTimer);
        draftTimer = setTimeout(() => {
            _saveDraftNow();
        }, 1000);
    }

    function invalidateInFlightComputation() {
        revision.value++;
        epicycleRevision++;
        basesRevision++;
        api.abortInflight(["extractContour", "computeEpicycles", "computeBases", "getContour"]);
    }

    async function _saveDraftNow() {
        if (!imageSlug.value) return;
        const raw: WorkspaceDraft = structuredClone({
            imageSlug: imageSlug.value,
            contour: contour.value,
            contourSettings: toRaw(contourSettings.value),
            animationSettings: toRaw(animationSettings.value),
            epicycleData: epicycleData.value,
            basesData: basesData.value,
            savedSnapshots: [],
            lastOpenedAt: new Date().toISOString(),
        });
        await saveDraft(raw).catch((e) => { console.warn("[draft] save failed:", e); });
    }

    watch([contourSettings, animationSettings], scheduleDraftSave, { deep: true });

    // Methods
    async function uploadImage(file: File) {
        loading.value = true;
        error.value = null;
        try {
            invalidateInFlightComputation();
            contour.value = null;
            epicycleData.value = null;
            basesData.value = null;
            // Always upload: store_image_asset deduplicates by sha256 and
            // regenerates the thumbnail with current processing (EXIF transpose).
            // Skipping the upload on hash match would leave stale thumbnails.
            const meta = await api.uploadImage(file);
            imageSlug.value = meta.image_slug;
            imageMeta.value = meta;
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
        epicycleRevision++;
        basesRevision++;
        api.abortInflight(["computeEpicycles", "computeBases", "getContour"]);
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
                let draftContour = draft.contour;
                // Re-fetch contour from API if draft is missing image_bounds
                // (triggers lazy backfill on the backend).
                if (draftContour && !draftContour.image_bounds) {
                    try {
                        draftContour = await api.getContour(draftContour.contour_hash);
                    } catch {
                        // keep stale draft contour if API fetch fails
                    }
                    if (revision.value !== rev) return;
                }
                contour.value = draftContour ? markRaw(draftContour) : null;
                contourSettings.value = {
                    ...defaultContourSettings(),
                    ...draft.contourSettings,
                };
                animationSettings.value = {
                    ...defaultAnimationSettings(),
                    ...draft.animationSettings,
                };
                epicycleData.value = draft.epicycleData ? markRaw(draft.epicycleData) : null;
                basesData.value = draft.basesData ? markRaw(draft.basesData) : null;
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
        epicycleRevision++;
        basesRevision++;
        api.abortInflight(["computeEpicycles", "computeBases", "getContour"]);
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
            contour.value = markRaw(contourAsset);
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
        beginCompute();
        error.value = null;
        const rev = ++revision.value;
        try {
            const result = await api.extractContour(
                imageSlug.value,
                contourSettings.value,
            );
            if (revision.value !== rev) return;
            contour.value = markRaw(result);
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Contour extraction failed";
            throw e;
        } finally {
            endCompute();
        }
    }

    async function saveContourPoints(points: { x: number[]; y: number[] }) {
        if (!imageSlug.value) return;
        beginCompute();
        error.value = null;
        try {
            epicycleRevision++;
            basesRevision++;
            api.abortInflight(["computeEpicycles", "computeBases"]);
            const result = await api.saveContour(imageSlug.value, points);
            contour.value = markRaw(result);
            epicycleData.value = null;
            basesData.value = null;
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Failed to save contour";
            throw e;
        } finally {
            endCompute();
        }
    }

    async function runComputeEpicycles() {
        if (!contour.value) return;
        beginCompute();
        error.value = null;
        const rev = ++epicycleRevision;
        try {
            const result = await api.computeEpicycles(
                contour.value.contour_hash,
                {
                    n_harmonics: contourSettings.value.n_harmonics,
                    n_points: contourSettings.value.n_points,
                },
            );
            if (epicycleRevision !== rev) return;
            epicycleData.value = markRaw(result);
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Epicycle computation failed";
            throw e;
        } finally {
            endCompute();
        }
    }

    async function runComputeBases() {
        if (!contour.value) return;
        beginCompute();
        error.value = null;
        const rev = ++basesRevision;
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
            if (basesRevision !== rev) return;
            basesData.value = markRaw(result);
            scheduleDraftSave();
        } catch (e: any) {
            if (!api.isAbortError(e))
                error.value = e.message ?? "Bases computation failed";
            throw e;
        } finally {
            endCompute();
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
        _computeDepth = 0;
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
        beginCompute,
        endCompute,
        invalidateInFlightComputation,
        defaultContourSettings,
        defaultAnimationSettings,
    };
});

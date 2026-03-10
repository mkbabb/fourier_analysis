import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type {
    SessionData,
    ContourSettings,
    AnimationSettings,
    EpicycleData,
    AnimationData,
    ContourData,
} from "@/lib/types";
import * as api from "@/lib/api";
import { isAbortError } from "@/lib/api";
import { router } from "@/router";

export const useSessionStore = defineStore("session", () => {
    const session = ref<SessionData | null>(null);
    const epicycleData = ref<EpicycleData | null>(null);
    const basesData = ref<AnimationData | null>(null);
    const contourData = ref<ContourData | null>(null);
    const loading = ref(false);
    const computing = ref(false);
    const error = ref<string | null>(null);

    const slug = computed(() => session.value?.slug ?? null);
    const hasImage = computed(() => session.value?.has_image ?? false);
    /** Bumped on each image upload to bust browser cache on the image URL. */
    const imageVersion = ref(0);

    /** True if the error is transient (503, network) and data should be preserved. */
    function isTransient(e: any): boolean {
        return e.message?.includes("503") || e.message?.includes("Failed to fetch");
    }

    async function create() {
        loading.value = true;
        error.value = null;
        try {
            session.value = await api.createSession();
            localStorage.setItem("fourier_last_slug", session.value.slug);
            router.replace(`/s/${session.value.slug}`);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
        } finally {
            loading.value = false;
        }
    }

    async function load(sessionSlug: string) {
        loading.value = true;
        error.value = null;
        try {
            session.value = await api.getSession(sessionSlug);
            localStorage.setItem("fourier_last_slug", sessionSlug);
            router.replace(`/s/${sessionSlug}`);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
            session.value = null;
            localStorage.removeItem("fourier_last_slug");
        } finally {
            loading.value = false;
        }
    }

    async function updateSettings(update: {
        parameters?: Partial<ContourSettings>;
        animation_settings?: Partial<AnimationSettings>;
    }) {
        if (!slug.value) return;
        try {
            session.value = await api.updateSession(slug.value, update);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
        }
    }

    async function uploadImage(file: File) {
        loading.value = true;
        error.value = null;
        try {
            const newSession = await api.createSession();
            session.value = newSession;

            const uploadResult = await api.uploadImage(newSession.slug, file);

            const activeSlug = uploadResult.existing && uploadResult.slug
                ? uploadResult.slug
                : newSession.slug;

            session.value = await api.getSession(activeSlug);
            localStorage.setItem("fourier_last_slug", activeSlug);
            router.replace(`/s/${activeSlug}`);

            epicycleData.value = null;
            basesData.value = null;
            contourData.value = null;
            imageVersion.value++;
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
        } finally {
            loading.value = false;
        }
    }

    async function runContours(params?: Partial<ContourSettings>) {
        if (!slug.value) return;
        loading.value = true;
        error.value = null;
        try {
            contourData.value = await api.computeContours(slug.value, params);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
        } finally {
            loading.value = false;
        }
    }

    async function runEpicycles(params?: {
        n_harmonics?: number;
        n_points?: number;
    }) {
        if (!slug.value) return;
        loading.value = true;
        error.value = null;
        try {
            epicycleData.value = await api.computeEpicycles(slug.value, params);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
            if (!isTransient(e)) epicycleData.value = null;
        } finally {
            loading.value = false;
        }
    }

    async function runBases(params?: {
        max_degree?: number;
        n_points?: number;
        levels?: number[];
        n_eval?: number;
    }) {
        if (!slug.value) return;
        loading.value = true;
        error.value = null;
        try {
            basesData.value = await api.computeBases(slug.value, params);
        } catch (e: any) {
            if (isAbortError(e)) return;
            error.value = e.message;
            if (!isTransient(e)) basesData.value = null;
        } finally {
            loading.value = false;
        }
    }

    return {
        session,
        slug,
        hasImage,
        epicycleData,
        basesData,
        contourData,
        loading,
        computing,
        error,
        imageVersion,
        create,
        load,
        updateSettings,
        uploadImage,
        runContours,
        runEpicycles,
        runBases,
    };
});

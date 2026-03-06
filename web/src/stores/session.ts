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

export const useSessionStore = defineStore("session", () => {
    const session = ref<SessionData | null>(null);
    const epicycleData = ref<EpicycleData | null>(null);
    const basesData = ref<AnimationData | null>(null);
    const contourData = ref<ContourData | null>(null);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const slug = computed(() => session.value?.slug ?? null);
    const hasImage = computed(() => session.value?.has_image ?? false);

    async function create() {
        loading.value = true;
        error.value = null;
        try {
            session.value = await api.createSession();
        } catch (e: any) {
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
        } catch (e: any) {
            error.value = e.message;
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
            error.value = e.message;
        }
    }

    async function uploadImage(file: File) {
        if (!slug.value) return;
        loading.value = true;
        error.value = null;
        try {
            await api.uploadImage(slug.value, file);
            // Refresh session to get has_image=true
            session.value = await api.getSession(slug.value);
        } catch (e: any) {
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
            error.value = e.message;
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
            error.value = e.message;
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
        error,
        create,
        load,
        updateSettings,
        uploadImage,
        runContours,
        runEpicycles,
        runBases,
    };
});

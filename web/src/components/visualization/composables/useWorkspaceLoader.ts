import { ref, watch, onMounted } from "vue";
import type { Ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useWorkspaceStore } from "@/stores/workspace";
import { useAnimationStore } from "@/stores/animation";
import type { EasingName } from "@/stores/animation";
import { useToast } from "@/composables/useToast";
import { isAbortError } from "@/lib/api";
import { CONTOUR_DEFAULTS } from "@/lib/defaults";

export function useWorkspaceLoader(activeBases: Ref<string[]>) {
    const route = useRoute();
    const router = useRouter();
    const store = useWorkspaceStore();
    const anim = useAnimationStore();
    const { toast } = useToast();

    // Seed contour settings from workspace (defaults applied immediately)
    const nHarmonics = ref(store.contourSettings?.n_harmonics ?? CONTOUR_DEFAULTS.n_harmonics);
    const nPoints = ref(store.contourSettings?.n_points ?? 1024);

    // Route-based loading on mount
    onMounted(async () => {
        const imageSlug = route.params.imageSlug as string | undefined;
        const snapshotHash = route.params.snapshotHash as string | undefined;
        if (imageSlug && snapshotHash) {
            await store.loadSnapshot(imageSlug, snapshotHash);
        } else if (imageSlug) {
            await store.loadWorkspace(imageSlug);
        } else if (store.imageSlug) {
            router.replace(`/w/${store.imageSlug}`);
        }
    });

    // Route param watcher for gallery navigation.
    // Skips if the slug already matches (e.g., after uploadImage pushed the route).
    watch(
        () => [route.params.imageSlug, route.params.snapshotHash],
        async ([newSlug, newHash]) => {
            const slug = newSlug as string | undefined;
            const hash = newHash as string | undefined;
            if (!slug) {
                if (store.imageSlug) router.replace(`/w/${store.imageSlug}`);
                return;
            }
            // Skip if we already have this workspace loaded (uploadImage just set it)
            if (slug === store.imageSlug && !hash) return;
            if (slug && hash) {
                await store.loadSnapshot(slug, hash);
            } else if (slug) {
                await store.loadWorkspace(slug);
            }
        },
    );

    // Seed animation settings from workspace (once)
    watch(
        () => store.animationSettings,
        (as) => {
            if (as?.active_bases?.length) {
                activeBases.value = [...as.active_bases];
            }
            if (as?.easing) anim.easing = as.easing as EasingName;
            if (as?.speed) anim.speed = as.speed;
        },
        { once: true },
    );

    // Seed contour settings from workspace (once)
    watch(
        () => store.contourSettings,
        (cs) => {
            if (cs) {
                nHarmonics.value = cs.n_harmonics ?? CONTOUR_DEFAULTS.n_harmonics;
                nPoints.value = cs.n_points ?? 1024;
            }
        },
        { once: true },
    );

    // Reset harmonics on new image
    watch(
        () => store.imageSlug,
        () => {
            nHarmonics.value = CONTOUR_DEFAULTS.n_harmonics;
        },
    );

    // Auto-compute epicycles when a new contour arrives without epicycleData.
    // Only watches contour (not computing) to avoid re-trigger loops from the
    // shared `computing` flag toggling during parallel compute calls.
    watch(
        () => store.contour,
        (contour) => {
            if (contour && !store.epicycleData && !store.computing) {
                store.computeEpicycles().catch((e) => {
                    if (!isAbortError(e)) {
                        console.warn("[auto-compute] epicycles failed:", e);
                    }
                });
            }
        },
        { immediate: true },
    );

    // Auto-play when computation data first arrives.
    // Does NOT override the user's basis selection on recomputes.
    let hadDataBefore = false;
    watch(
        () => [store.epicycleData, store.basesData] as const,
        ([epicData, basesData]) => {
            if (!epicData && !basesData) {
                hadDataBefore = false;
                return;
            }
            if (!hadDataBefore) {
                hadDataBefore = true;
                // First data arrival: ensure fourier-epicycles is selected
                if (!activeBases.value.includes("fourier-epicycles")) {
                    activeBases.value = [
                        "fourier-epicycles",
                        ...activeBases.value.filter((b) => !b.startsWith("fourier")),
                    ];
                }
            }
            // Start playing if not already
            if (!anim.playing) {
                anim.reset();
                anim.play();
            }
        },
        { immediate: true },
    );

    // Error toast
    watch(
        () => store.error,
        (err) => {
            if (err && store.imageSlug) {
                toast(err, "error");
                store.error = null;
            }
        },
    );

    return { nHarmonics, nPoints };
}

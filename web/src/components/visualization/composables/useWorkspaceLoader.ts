import { ref, watch, onMounted } from "vue";
import type { Ref } from "vue";
import { useRoute } from "vue-router";
import { useWorkspaceStore } from "@/stores/workspace";
import { useAnimationStore } from "@/stores/animation";
import type { EasingName } from "@/stores/animation";
import { useToast } from "@/composables/useToast";

export function useWorkspaceLoader(activeBases: Ref<string[]>) {
    const route = useRoute();
    const store = useWorkspaceStore();
    const anim = useAnimationStore();
    const { toast } = useToast();

    // Seed contour settings from workspace (defaults applied immediately)
    const nHarmonics = ref(store.contourSettings?.n_harmonics ?? 50);
    const nPoints = ref(store.contourSettings?.n_points ?? 1024);

    // Route-based loading on mount
    onMounted(async () => {
        const imageSlug = route.params.imageSlug as string | undefined;
        const snapshotHash = route.params.snapshotHash as string | undefined;
        if (imageSlug && snapshotHash) {
            await store.loadSnapshot(imageSlug, snapshotHash);
        } else if (imageSlug) {
            await store.loadWorkspace(imageSlug);
        }
    });

    // Route param watcher for gallery navigation.
    // Skips if the slug already matches (e.g., after uploadImage pushed the route).
    watch(
        () => [route.params.imageSlug, route.params.snapshotHash],
        async ([newSlug, newHash]) => {
            const slug = newSlug as string | undefined;
            const hash = newHash as string | undefined;
            if (!slug) return;
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
                // Normalize legacy "fourier" → "fourier-epicycles"
                activeBases.value = as.active_bases.map((b: string) =>
                    b === "fourier" ? "fourier-epicycles" : b,
                );
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
                nHarmonics.value = cs.n_harmonics ?? 50;
                nPoints.value = cs.n_points ?? 1024;
            }
        },
        { once: true },
    );

    // Reset harmonics on new image
    watch(
        () => store.imageSlug,
        () => {
            nHarmonics.value = 50;
        },
    );

    // Auto-compute epicycles when contour exists but epicycleData doesn't.
    // Watch both contour AND computing so we retry after any in-flight computation finishes.
    watch(
        () => [store.contour, store.computing] as const,
        ([contour, computing]) => {
            if (contour && !store.epicycleData && !computing) {
                store.computeEpicycles().catch((e) => {
                    console.warn("[auto-compute] epicycles failed:", e);
                });
            }
        },
        { immediate: true },
    );

    // Auto-play when any computation data arrives (epicycles or bases).
    // Ensures fourier-epicycles is active and animation is playing.
    watch(
        () => [store.epicycleData, store.basesData] as const,
        ([epicData, basesData]) => {
            if (!epicData && !basesData) return;
            // Always ensure fourier-epicycles is selected
            if (!activeBases.value.includes("fourier-epicycles")) {
                activeBases.value = [
                    "fourier-epicycles",
                    ...activeBases.value.filter((b) => !b.startsWith("fourier")),
                ];
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

import { ref, watch } from "vue";
import { useWorkspaceStore } from "@/stores/workspace";
import { overlayUrl } from "@/lib/api";
import type { CanvasSurface, ViewTransform } from "../lib/canvas-drawing";

const MAX_CACHE_SIZE = 10;

// Module-scoped cache survives component unmount/remount (e.g. gallery → visualizer)
const cache = new Map<string, HTMLImageElement>();

/**
 * Derive the resize value from image_bounds.
 * image_bounds = {-w/2, w/2, -h/2, h/2} → max(w, h) == resize parameter.
 */
function resizeFromBounds(store: ReturnType<typeof useWorkspaceStore>): number {
    const ib = store.contour?.image_bounds;
    if (!ib) return store.contourSettings?.resize ?? 768;
    return Math.round(Math.max(ib.maxX - ib.minX, ib.maxY - ib.minY));
}

/**
 * Loads the resized overlay image (matching contour-extraction dimensions)
 * and draws it behind the animation using the authoritative `image_bounds`
 * from the contour document — pixel-perfect alignment with contour data space.
 */
export function useImageOverlay(onImageLoaded?: () => void) {
    const store = useWorkspaceStore();
    const loading = ref(false);
    let currentImage: HTMLImageElement | null = null;

    function cacheKey(): string | null {
        if (!store.imageSlug) return null;
        return `${store.imageSlug}:${resizeFromBounds(store)}`;
    }

    watch(
        () => [store.imageSlug, store.contour] as const,
        () => {
            const key = cacheKey();
            if (!key) { currentImage = null; loading.value = false; return; }
            if (cache.has(key)) {
                currentImage = cache.get(key)!;
                loading.value = false;
                onImageLoaded?.();
                return;
            }
            currentImage = null;
            loading.value = true;
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                if (cache.size >= MAX_CACHE_SIZE) {
                    const oldest = cache.keys().next().value!;
                    cache.delete(oldest);
                }
                cache.set(key, img);
                if (cacheKey() === key) {
                    currentImage = img;
                    loading.value = false;
                    onImageLoaded?.();
                }
            };
            img.onerror = () => {
                if (cacheKey() === key) {
                    currentImage = null;
                    loading.value = false;
                }
            };
            img.src = overlayUrl(store.imageSlug!, resizeFromBounds(store));
        },
        { immediate: true },
    );

    function drawImageOverlay(s: CanvasSurface, view: ViewTransform) {
        if (!currentImage) return;

        const bounds = store.contour?.image_bounds;
        if (!bounds) return;

        const [sx1, sy1] = view.toScreen(bounds.minX, bounds.maxY);
        const [sx2, sy2] = view.toScreen(bounds.maxX, bounds.minY);
        const boxW = sx2 - sx1;
        const boxH = sy2 - sy1;
        if (boxW <= 0 || boxH <= 0) return;

        s.ctx.save();
        s.ctx.globalAlpha = 0.28;
        s.ctx.drawImage(currentImage, sx1, sy1, boxW, boxH);
        s.ctx.restore();
    }

    return { drawImageOverlay, loading };
}

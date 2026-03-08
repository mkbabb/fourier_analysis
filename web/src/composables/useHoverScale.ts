/**
 * Composable for smooth hover-scale animation with rAF interpolation.
 * Returns mouse handlers and the current interpolated scale value.
 */
export function useHoverScale(
    baseScale: number,
    hoverScale: number,
    hitTest: (mouseX: number, mouseY: number) => boolean,
    getContainerRect: () => DOMRect | undefined,
    onUpdate: () => void,
) {
    let mouseX = -1;
    let mouseY = -1;
    let current = baseScale;
    let target = baseScale;
    let rafId: number | null = null;

    function tick() {
        const diff = target - current;
        if (Math.abs(diff) < 0.002) {
            current = target;
            rafId = null;
            onUpdate();
            return;
        }
        current += diff * 0.12;
        onUpdate();
        rafId = requestAnimationFrame(tick);
    }

    function onMouseMove(e: MouseEvent) {
        const rect = getContainerRect();
        if (!rect) return;
        mouseX = e.clientX - rect.left;
        mouseY = e.clientY - rect.top;

        const inRegion = hitTest(mouseX, mouseY);
        const newTarget = inRegion ? hoverScale : baseScale;
        if (newTarget !== target) {
            target = newTarget;
            if (!rafId) rafId = requestAnimationFrame(tick);
        }
    }

    function onMouseLeave() {
        mouseX = -1;
        mouseY = -1;
        if (target !== baseScale) {
            target = baseScale;
            if (!rafId) rafId = requestAnimationFrame(tick);
        }
    }

    function getScale(): number {
        return current;
    }

    function cleanup() {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
    }

    return { onMouseMove, onMouseLeave, getScale, cleanup };
}

<script setup lang="ts">
import { ref, watch } from "vue";
import { useWorkspaceStore } from "@/stores/workspace";
import { useAnimationStore } from "@/stores/animation";
import { fourierPositionsAt, evaluateFourier } from "@/lib/bases";
import { VIZ_COLORS, hexToRgba } from "@/lib/colors";
import { goldenShimmerAlpha, clearShimmer } from "@/lib/golden-shimmer";
import { basisDisplay } from "./lib/basis-display";
import type { BasisComponent } from "@/lib/types";
import type { CanvasSurface, ViewTransform, EpicycleBbox } from "./lib/canvas-drawing";
import {
    drawGrid,
    drawGhostPath,
    drawPlaceholder,
    drawTipDot,
    drawEpicycleCircles,
    drawConnectingLine,
    drawBasisLabels,
    TrailManager,
    BASE_EPICYCLE_SCALE,
    HOVER_EPICYCLE_SCALE,
    computeStableEpicycleBbox,
    computeEpicycleFit,
    isMouseInEpicycleBounds,
    epicycleAlphaFromScale,
} from "./lib/canvas-drawing";
import type { EpicycleFit } from "./lib/canvas-drawing";
import { useCanvasSetup } from "./composables/useCanvasSetup";
import { useCanvasHover } from "./composables/useCanvasHover";
import { useImageOverlay } from "./composables/useImageOverlay";
import { useViewTransform } from "./composables/useViewTransform";

const props = withDefaults(
    defineProps<{
        activeBases?: string[];
        showGhost?: boolean;
        showImageOverlay?: boolean;
    }>(),
    { activeBases: () => ["fourier-epicycles"], showGhost: true, showImageOverlay: false },
);

const store = useWorkspaceStore();
const anim = useAnimationStore();
const canvasRef = ref<HTMLCanvasElement>();
const containerRef = ref<HTMLDivElement>();

const maxCircles = ref(80);

// ── Cached epicycle state ──
let stableEpicycleBbox: EpicycleBbox | null = null;
let baseFitCenter: { cx: number; cy: number; baseFitScale: number } | null = null;
let epicycleBounds = { x: 0, y: 0, w: 0, h: 0 };

// ── Trail ──
const trail = new TrailManager();

// ── Canvas setup ──
const { surface, setupCanvas } = useCanvasSetup(canvasRef, containerRef, (s) => {
    stableEpicycleBbox = null;
    baseFitCenter = null;
    if (store.epicycleData) drawFrame();
    else drawPlaceholderFrame(s);
});

// ── Hover ──
const hover = useCanvasHover({
    baseScale: BASE_EPICYCLE_SCALE,
    hoverScale: HOVER_EPICYCLE_SCALE,
    isInEpicycleRegion: () => {
        const [mx, my] = hover.getMousePos();
        return isMouseInEpicycleBounds(mx, my, epicycleBounds);
    },
    getContainerEl: () => containerRef.value,
    onRedraw: () => { if (surface.value) drawFrame(); },
});

// ── View transform (extracted composable) ──
const { getViewTransform } = useViewTransform();

// ── Image overlay (extracted composable) ──
const { drawImageOverlay } = useImageOverlay(() => {
    if (surface.value) drawFrame();
});

// ── Draw placeholder ──
function drawPlaceholderFrame(s: CanvasSurface) {
    drawPlaceholder(s, !!store.imageMeta);
}

// ── Main draw frame ──
function drawFrame() {
    const s = surface.value;
    if (!s) return;
    const data = store.epicycleData;
    const basesData = store.basesData;
    if (!data && !basesData) { drawPlaceholderFrame(s); return; }

    s.ctx.clearRect(0, 0, s.width, s.height);
    const view = getViewTransform(s);

    // Background grid
    drawGrid(s, view);

    // Image overlay (behind curves)
    if (props.showImageOverlay) {
        drawImageOverlay(s, view);
    }

    const hasEpicycles = props.activeBases.includes("fourier-epicycles");
    const onlyEpicycles = hasEpicycles && props.activeBases.length === 1;

    if (onlyEpicycles && data) {
        drawEpicycleFrame(s, data, view);
    } else {
        drawMultiBasesFrame(s, view);
    }
}

// ── Single epicycle mode ──
function drawEpicycleFrame(
    s: CanvasSurface,
    data: typeof store.epicycleData & {},
    view: ViewTransform,
) {
    const hoveredBasis = hover.getHoveredBasis();
    const epicycleHovered = hoveredBasis === "fourier-epicycles";
    const trailColor = epicycleHovered ? VIZ_COLORS.golden : VIZ_COLORS.fourier;

    // Ghost path
    if (props.showGhost) {
        drawGhostPath(s, view, data.path.x, data.path.y, true);
    }

    const components: BasisComponent[] = data.components;
    const nVis = Math.min(maxCircles.value, components.length);

    // All components for accurate tip position
    const allPositions = fourierPositionsAt(components, anim.t, components.length);
    const tip = allPositions[allPositions.length - 1];

    // Trail — golden when hovered
    trail.update(anim.t, tip[0], tip[1], anim.scrubbing, components);
    trail.draw(s, view, trailColor);

    // Epicycle circles
    const visPositions = fourierPositionsAt(components, anim.t, nVis);
    const isDesktop = s.width >= 768;
    const currentScale = hover.getScale();
    const eAlpha = epicycleAlphaFromScale(currentScale);

    if (!stableEpicycleBbox) {
        stableEpicycleBbox = computeStableEpicycleBbox(components, nVis, view.toScreen, view.scale);
    }

    let fit: EpicycleFit | null = null;
    if (isDesktop && nVis > 0) {
        const result = computeEpicycleFit(stableEpicycleBbox, s, currentScale, baseFitCenter);
        if (result) {
            fit = result.fit;
            baseFitCenter = result.baseFitCenter;
        }
    }

    // Golden shimmer on epicycle circles when hovered
    if (epicycleHovered) {
        s.ctx.globalAlpha = goldenShimmerAlpha();
    }
    drawEpicycleCircles(s, view, visPositions, components, nVis, fit, eAlpha, { circle: 4, arm: 3.5 }, epicycleHovered ? VIZ_COLORS.golden : undefined);
    s.ctx.globalAlpha = 1;

    // Update epicycle bounds for hover detection
    if (fit) {
        epicycleBounds = {
            x: fit.targetCX - fit.scaledW / 2,
            y: fit.targetCY - fit.scaledH / 2,
            w: fit.scaledW,
            h: fit.scaledH,
        };
    } else {
        epicycleBounds = { x: 0, y: 0, w: 0, h: 0 };
    }

    // Connecting line
    if (fit) {
        drawConnectingLine(s, view, visPositions, tip[0], tip[1], fit, eAlpha);
    }

    // Tip dot
    drawTipDot(s, view, tip[0], tip[1]);

    // Label with hit regions for hover detection
    const level = Math.max(1, Math.ceil(anim.easedT * components.length));
    const { hitRegions } = drawBasisLabels(s, ["fourier-epicycles"], `N = ${level}`, hoveredBasis);
    hover.setLabelHitRegions(hitRegions);
}

// ── Multi-basis mode ──
function drawMultiBasesFrame(s: CanvasSurface, view: ViewTransform) {
    const { ctx, width, height } = s;
    const basesData = store.basesData;
    const epicycleData = store.epicycleData;
    const hoveredBasis = hover.getHoveredBasis();

    // Ghost path
    if (props.showGhost) {
        let origX: number[] | undefined;
        let origY: number[] | undefined;
        if (basesData) {
            origX = basesData.original.x;
            origY = basesData.original.y;
        } else if (epicycleData) {
            origX = epicycleData.path.x;
            origY = epicycleData.path.y;
        }
        if (origX && origY) {
            drawGhostPath(s, view, origX, origY);
        }
    }

    // Current level — global easing drives one continuous flow,
    // linear interpolation between adjacent precomputed levels.
    let level = 1;
    let levelFrac = 0;
    let levelNext = 1;
    if (basesData && basesData.levels.length > 0) {
        const levels = basesData.levels;
        const pos = anim.easedT * (levels.length - 1);
        const lo = Math.floor(pos);
        const hi = Math.min(lo + 1, levels.length - 1);
        levelFrac = pos - lo;  // linear — global easing already shaped the curve
        level = levels[lo];
        levelNext = levels[hi];
    } else if (epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        level = Math.max(1, Math.ceil(anim.easedT * components.length));
        levelNext = level;
    }

    const clipMinX = -width;
    const clipMaxX = 2 * width;
    const clipMinY = -height;
    const clipMaxY = 2 * height;

    // Draw each active basis curve
    for (const basisKey of props.activeBases) {
        const basisName = basisKey.startsWith("fourier") ? "fourier" : basisKey;
        const cfg = basisDisplay[basisName];
        if (!cfg) continue;

        const isHovered = hoveredBasis === basisKey;
        const shimmer = isHovered ? goldenShimmerAlpha() : 0;
        ctx.beginPath();
        ctx.strokeStyle = isHovered ? VIZ_COLORS.golden : cfg.color;
        ctx.lineWidth = isHovered ? 4 : 3;
        ctx.globalAlpha = isHovered ? shimmer : 0.85;
        if (isHovered) {
            ctx.shadowColor = hexToRgba(VIZ_COLORS.golden, shimmer * 0.5);
            ctx.shadowBlur = 10;
        }
        ctx.lineJoin = "round";
        ctx.lineCap = "round";

        // Look up partial sum data
        const sumsForBasis = basisName === "fourier"
            ? basesData?.partial_sums?.fourier
            : basesData?.partial_sums[basisName];
        const sumLo = (sumsForBasis as any)?.[level] ?? (sumsForBasis as any)?.[String(level)];
        const sumHi = levelFrac > 0.001
            ? ((sumsForBasis as any)?.[levelNext] ?? (sumsForBasis as any)?.[String(levelNext)])
            : null;

        if (sumLo) {
            const doInterp = sumHi && sumHi.x.length === sumLo.x.length && levelFrac > 0.001;
            const isPolynomial = basisName !== "fourier";
            let needsMove = true;
            for (let i = 0; i < sumLo.x.length; i++) {
                let px = sumLo.x[i];
                let py = sumLo.y[i];
                if (doInterp) {
                    px += levelFrac * (sumHi.x[i] - px);
                    py += levelFrac * (sumHi.y[i] - py);
                }
                const [sx, sy] = view.toScreen(px, py);
                if (isPolynomial && (sx < clipMinX || sx > clipMaxX || sy < clipMinY || sy > clipMaxY)) {
                    needsMove = true;
                    continue;
                }
                if (needsMove || i === 0) {
                    ctx.moveTo(sx, sy);
                    needsMove = false;
                } else {
                    ctx.lineTo(sx, sy);
                }
            }
        } else if (basisName === "fourier" && epicycleData) {
            // Fallback: client-side evaluation
            const components: BasisComponent[] = epicycleData.components;
            const nTerms = Math.min(level, components.length);
            const nEval = 800;
            for (let i = 0; i <= nEval; i++) {
                const tEval = i / nEval;
                const [re, im] = evaluateFourier(components, tEval, nTerms);
                const [sx, sy] = view.toScreen(re, im);
                if (i === 0) ctx.moveTo(sx, sy);
                else ctx.lineTo(sx, sy);
            }
        }
        ctx.stroke();
        clearShimmer(ctx);
    }

    // Epicycle trail + tip + hover overlay when fourier-epicycles is active
    const hasEpicyclesMode = props.activeBases.includes("fourier-epicycles");
    if (hasEpicyclesMode && epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        const nVis = Math.min(maxCircles.value, components.length);
        const allPositions = fourierPositionsAt(components, anim.t, components.length);
        const tip = allPositions[allPositions.length - 1];

        const epicycleHovered = hoveredBasis === "fourier-epicycles";
        const epicycleColor = epicycleHovered ? VIZ_COLORS.golden : VIZ_COLORS.fourier;

        // Trail
        trail.update(anim.t, tip[0], tip[1], anim.scrubbing, components);
        trail.draw(s, view, epicycleColor);

        // Tip dot
        drawTipDot(s, view, tip[0], tip[1]);

        // Epicycle overlay
        const visPositions = fourierPositionsAt(components, anim.t, nVis);
        const isDesktop = width >= 768;
        const currentScale = hover.getScale();
        const eAlpha = epicycleAlphaFromScale(currentScale);

        if (!stableEpicycleBbox) {
            stableEpicycleBbox = computeStableEpicycleBbox(components, nVis, view.toScreen, view.scale);
        }

        let fit: EpicycleFit | null = null;
        if (isDesktop && nVis > 0) {
            const result = computeEpicycleFit(stableEpicycleBbox, s, currentScale, baseFitCenter);
            if (result) {
                fit = result.fit;
                baseFitCenter = result.baseFitCenter;
            }
        }

        drawEpicycleCircles(s, view, visPositions, components, nVis, fit, eAlpha, { circle: 5, arm: 4.5 }, epicycleHovered ? epicycleColor : null);

        if (fit) {
            epicycleBounds = {
                x: fit.targetCX - fit.scaledW / 2,
                y: fit.targetCY - fit.scaledH / 2,
                w: fit.scaledW,
                h: fit.scaledH,
            };
            drawConnectingLine(s, view, visPositions, tip[0], tip[1], fit, eAlpha);
        }
    }

    // Labels
    const { hitRegions } = drawBasisLabels(s, props.activeBases, `N = ${level}`, hoveredBasis);
    hover.setLabelHitRegions(hitRegions);
}

// ── Watchers (split: epicycle vs bases) ──
// Watcher A — epicycle identity + epicycle-mode visibility.
// Trail is only cleared when the epicycle data itself changes or the
// epicycle layer is toggled, NOT when basesData arrives.
watch(
    [() => store.epicycleData, () => props.activeBases.includes("fourier-epicycles")],
    () => {
        trail.clearTrail();
        stableEpicycleBbox = null;
        baseFitCenter = null;

        if (store.epicycleData) {
            trail.precompute(store.epicycleData.components);
        } else {
            trail.reset();
        }

        if (!surface.value) {
            setupCanvas();
        } else {
            drawFrame();
        }
    },
);

// Watcher B — bases data + full activeBases list.
// Only invalidates the basis fit center (layout may have changed);
// does NOT touch trail so epicycle animation stays continuous.
watch(
    [() => store.basesData, () => props.activeBases],
    () => {
        baseFitCenter = null;

        if (!surface.value) {
            setupCanvas();
        } else {
            drawFrame();
        }
    },
);

// Render watcher: fires at 60 fps while animating.  Keep it to the bare
// minimum: animation clock ticks and the two display-toggle props.
// basesData is intentionally NOT here — it belongs in the data watcher above.
watch(
    [() => anim.t, () => anim.easedT, () => props.showGhost, () => props.showImageOverlay],
    () => {
        if (surface.value) drawFrame();
    },
);

// ── Export ──
function exportFrame(options: Record<string, boolean> = {}) {
    if (!canvasRef.value || !surface.value) return;
    const s = surface.value;

    const {
        withGrid: showGrid = true,
        withLabels: showLabels = true,
    } = options;

    // Create an offscreen canvas at the same resolution
    const offCanvas = document.createElement("canvas");
    offCanvas.width = canvasRef.value.width;
    offCanvas.height = canvasRef.value.height;
    const offCtx = offCanvas.getContext("2d")!;
    offCtx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);

    // Swap surface ctx temporarily
    const origCtx = s.ctx;
    (s as any).ctx = offCtx;

    const data = store.epicycleData;
    const basesData = store.basesData;
    if (data || basesData) {
        offCtx.clearRect(0, 0, s.width, s.height);
        const view = getViewTransform(s);
        if (showGrid) drawGrid(s, view);

        const hasEpic = props.activeBases.includes("fourier-epicycles");
        const onlyEpic = hasEpic && props.activeBases.length === 1;

        if (onlyEpic && data) {
            drawEpicycleFrame(s, data, view);
        } else {
            drawMultiBasesFrame(s, view);
        }

        if (!showLabels) {
            offCtx.clearRect(0, 0, 200, 100);
        }
    }

    // Restore
    (s as any).ctx = origCtx;

    const dataUrl = offCanvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `fourier-frame-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

defineExpose({ anim, exportFrame, drawImageOverlay });
</script>

<template>
    <div
        ref="containerRef"
        class="canvas-container cartoon-card"
        @mousemove="hover.onMouseMove"
        @mouseleave="hover.onMouseLeave"
        @click="hover.onClick"
    >
        <canvas ref="canvasRef" class="canvas-el" />
    </div>
</template>

<style scoped>
.canvas-container {
    position: relative;
    overflow: hidden;
    flex: 1;
    min-height: 0;
    user-select: none;
    -webkit-user-select: none;
}

.canvas-el {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    image-rendering: crisp-edges;
}
</style>

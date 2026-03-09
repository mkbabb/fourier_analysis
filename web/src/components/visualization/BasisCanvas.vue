<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from "vue";
import { easeInOutCubic } from "@mkbabb/value.js";
import { useSessionStore } from "@/stores/session";
import { useAnimationStore } from "@/stores/animation";
import { fourierPositionsAt, evaluateFourier } from "@/lib/bases";
import type { BasisComponent, AnimationData } from "@/lib/types";

const props = withDefaults(
    defineProps<{
        activeBases?: string[];
    }>(),
    { activeBases: () => ["fourier-epicycles"] },
);

const basisConfig: Record<string, { color: string; icon: string; label: string }> = {
    fourier: { color: "#ff3412", icon: "\u2131", label: "Fourier" },
    chebyshev: { color: "#3b82f6", icon: "T\u2099", label: "Chebyshev" },
    legendre: { color: "#a855f7", icon: "P\u2099", label: "Legendre" },
};

const store = useSessionStore();
const anim = useAnimationStore();
const canvasRef = ref<HTMLCanvasElement>();
const containerRef = ref<HTMLDivElement>();

const maxCircles = ref(80);
const showGhost = ref(true);

let ctx: CanvasRenderingContext2D | null = null;
let width = 0;
let height = 0;
let dpr = 1;
let resizeObserver: ResizeObserver | null = null;

// Mouse tracking for epicycle hover detection
let mouseX = -1;
let mouseY = -1;

// Legend hover: which basis key is hovered
let hoveredBasis: string | null = null;
// Store label hit regions for mouse detection
let labelHitRegions: { key: string; x: number; y: number; w: number; h: number }[] = [];
let shimmerRafId: number | null = null;

function startShimmer() {
    if (shimmerRafId) return;
    function shimmerTick() {
        if (!hoveredBasis) { shimmerRafId = null; return; }
        if (ctx && width > 0) drawFrame();
        shimmerRafId = requestAnimationFrame(shimmerTick);
    }
    shimmerRafId = requestAnimationFrame(shimmerTick);
}

function stopShimmer() {
    if (shimmerRafId) {
        cancelAnimationFrame(shimmerRafId);
        shimmerRafId = null;
    }
}

// Epicycles always visible at base size, grow on hover
const BASE_EPICYCLE_SCALE = 0.38;
const HOVER_EPICYCLE_SCALE = 0.55;
let currentEpicycleScale = BASE_EPICYCLE_SCALE;
let targetEpicycleScale = BASE_EPICYCLE_SCALE;
let hoverAnimFrame: number | null = null;

// Track the actual rendered bounding box of the epicycle region (screen coords)
let epicycleBounds = { x: 0, y: 0, w: 0, h: 0 };

// Cached stable epicycle bbox (computed once when data changes, not per-frame)
let stableEpicycleBbox: { minX: number; minY: number; maxX: number; maxY: number } | null = null;

/**
 * Compute a stable (time-invariant) bounding box for the epicycle chain
 * by sampling positions across the full animation cycle and taking the union
 * of all circle extents. This gives a tight but stable bound.
 */
function computeStableEpicycleBbox(
    components: BasisComponent[],
    nVis: number,
    toScreen: (x: number, y: number) => [number, number],
    scale: number,
): { minX: number; minY: number; maxX: number; maxY: number } {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const nSamples = 64;
    for (let s = 0; s <= nSamples; s++) {
        const t = s / nSamples;
        const positions = fourierPositionsAt(components, t, nVis);
        for (let i = 0; i < nVis; i++) {
            const [ccx, ccy] = toScreen(positions[i][0], positions[i][1]);
            const r = components[i].amplitude * scale;
            minX = Math.min(minX, ccx - r);
            minY = Math.min(minY, ccy - r);
            maxX = Math.max(maxX, ccx + r);
            maxY = Math.max(maxY, ccy + r);
        }
    }
    return { minX, minY, maxX, maxY };
}

// Cached base-scale fit center so hover scales from center, not from corner
let baseFitCenter: { cx: number; cy: number; baseFitScale: number } | null = null;

/**
 * Compute a transform that fits a raw-coordinate bounding box into
 * the bottom-left corner of the canvas. Uses BASE_EPICYCLE_SCALE for
 * positioning (cached), then applies currentEpicycleScale as a multiplier
 * so hover grows from center.
 * Returns null if the bbox is degenerate.
 */
function computeEpicycleFit(
    rawMinX: number, rawMinY: number, rawMaxX: number, rawMaxY: number,
) {
    const bboxW = rawMaxX - rawMinX;
    const bboxH = rawMaxY - rawMinY;
    if (bboxW <= 0 || bboxH <= 0) return null;

    const pad = 12;

    // Compute the base fit (at BASE_EPICYCLE_SCALE) — this determines the fixed center
    if (!baseFitCenter) {
        const baseRegionW = width * BASE_EPICYCLE_SCALE;
        const baseRegionH = height * BASE_EPICYCLE_SCALE;
        const bfs = Math.min(baseRegionW / bboxW, baseRegionH / bboxH);
        const baseScaledW = bboxW * bfs;
        const baseScaledH = bboxH * bfs;
        baseFitCenter = {
            cx: pad + baseScaledW / 2,
            cy: height - pad - baseScaledH / 2,
            baseFitScale: bfs,
        };
    }

    // Apply hover multiplier: scale around the cached center
    const hoverMul = currentEpicycleScale / BASE_EPICYCLE_SCALE;
    const fitScale = baseFitCenter.baseFitScale * hoverMul;
    const scaledW = bboxW * fitScale;
    const scaledH = bboxH * fitScale;

    // Raw bbox center
    const bboxCX = (rawMinX + rawMaxX) / 2;
    const bboxCY = (rawMinY + rawMaxY) / 2;

    // Target center = cached base center (doesn't move on hover)
    const targetCX = baseFitCenter.cx;
    const targetCY = baseFitCenter.cy;

    return { fitScale, bboxCX, bboxCY, targetCX, targetCY, scaledW, scaledH, pad };
}

function spectrumColor(i: number, total: number): string {
    // Non-linear mapping: stretch warm colors (red/orange/yellow), compress cool
    const t = i / Math.max(total - 1, 1);
    // Use a power curve to bias toward warm colors for high-amplitude components
    const curved = Math.pow(t, 0.6);
    const hue = (1 - curved) * 300;
    return `hsl(${hue}, 85%, 55%)`;
}

function setupCanvas() {
    if (!canvasRef.value || !containerRef.value) return;
    const rect = containerRef.value.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    dpr = window.devicePixelRatio || 1;
    width = rect.width;
    height = rect.height;
    stableEpicycleBbox = null; // Invalidate on resize
    baseFitCenter = null;

    canvasRef.value.width = Math.round(width * dpr);
    canvasRef.value.height = Math.round(height * dpr);
    canvasRef.value.style.width = `${width}px`;
    canvasRef.value.style.height = `${height}px`;

    ctx = canvasRef.value.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    if (store.epicycleData) {
        drawFrame();
    } else {
        drawPlaceholder();
    }
}

function getPathBounds() {
    // Use epicycleData path, or basesData original
    let xs: number[];
    let ys: number[];
    if (store.epicycleData) {
        xs = store.epicycleData.path.x;
        ys = store.epicycleData.path.y;
    } else if (store.basesData) {
        xs = store.basesData.original.x;
        ys = store.basesData.original.y;
    } else {
        return { cx: 0, cy: 0, scale: 1, rangeX: 1, rangeY: 1 };
    }

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;
    const margin = 0.15;
    const scale = Math.min(
        width / (rangeX * (1 + margin * 2)),
        height / (rangeY * (1 + margin * 2)),
    );

    return {
        cx: (minX + maxX) / 2,
        cy: (minY + maxY) / 2,
        scale,
        rangeX,
        rangeY,
    };
}


function isMouseInEpicycleRegion(): boolean {
    if (mouseX < 0 || mouseY < 0) return false;
    // Check if mouse is within the actual rendered epicycle bounding box
    const pad = 16;
    return mouseX >= epicycleBounds.x - pad &&
           mouseX <= epicycleBounds.x + epicycleBounds.w + pad &&
           mouseY >= epicycleBounds.y - pad &&
           mouseY <= epicycleBounds.y + epicycleBounds.h + pad;
}

function onCanvasMouseMove(e: MouseEvent) {
    const rect = containerRef.value?.getBoundingClientRect();
    if (!rect) return;
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;

    const inRegion = isMouseInEpicycleRegion();
    const newTarget = inRegion ? HOVER_EPICYCLE_SCALE : BASE_EPICYCLE_SCALE;
    if (newTarget !== targetEpicycleScale) {
        targetEpicycleScale = newTarget;
        if (!hoverAnimFrame) hoverAnimFrame = requestAnimationFrame(updateHoverScale);
    }

    // Check label hover
    let newHovered: string | null = null;
    for (const region of labelHitRegions) {
        if (mouseX >= region.x && mouseX <= region.x + region.w &&
            mouseY >= region.y && mouseY <= region.y + region.h) {
            newHovered = region.key;
            break;
        }
    }
    if (newHovered !== hoveredBasis) {
        hoveredBasis = newHovered;
        if (containerRef.value) {
            containerRef.value.style.cursor = hoveredBasis ? "pointer" : "";
        }
        if (hoveredBasis) startShimmer();
        else { stopShimmer(); if (ctx && width > 0) drawFrame(); }
    }
}

function onCanvasMouseLeave() {
    mouseX = -1;
    mouseY = -1;
    if (targetEpicycleScale !== BASE_EPICYCLE_SCALE) {
        targetEpicycleScale = BASE_EPICYCLE_SCALE;
        if (!hoverAnimFrame) hoverAnimFrame = requestAnimationFrame(updateHoverScale);
    }
    if (hoveredBasis) {
        hoveredBasis = null;
        if (containerRef.value) containerRef.value.style.cursor = "";
        if (ctx && width > 0) drawFrame();
    }
}

// Smooth hover animation
function updateHoverScale() {
    const diff = targetEpicycleScale - currentEpicycleScale;
    if (Math.abs(diff) < 0.002) {
        currentEpicycleScale = targetEpicycleScale;
        hoverAnimFrame = null;
        drawFrame();
        return;
    }
    currentEpicycleScale += diff * 0.12;
    drawFrame();
    hoverAnimFrame = requestAnimationFrame(updateHoverScale);
}

const trailX: number[] = [];
const trailY: number[] = [];
let lastTrailT = -1;

// Pre-computed trail for fast scrubbing
let precomputedTrailX: Float64Array | null = null;
let precomputedTrailY: Float64Array | null = null;
const TRAIL_RESOLUTION = 1200;

function precomputeTrail(components: BasisComponent[]) {
    const n = TRAIL_RESOLUTION;
    precomputedTrailX = new Float64Array(n + 1);
    precomputedTrailY = new Float64Array(n + 1);
    for (let i = 0; i <= n; i++) {
        const [re, im] = evaluateFourier(components, i / n);
        precomputedTrailX[i] = re;
        precomputedTrailY[i] = im;
    }
}

function drawGrid(
    toScreen: (x: number, y: number) => [number, number],
    cx: number,
    cy: number,
    scale: number,
) {
    if (!ctx) return;

    // Compute grid step in data space (~40px on screen)
    const rawStep = 40 / scale;
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
    const normalized = rawStep / magnitude;
    let step: number;
    if (normalized <= 2) step = 2 * magnitude;
    else if (normalized <= 5) step = 5 * magnitude;
    else step = 10 * magnitude;

    const halfW = width / (2 * scale);
    const halfH = height / (2 * scale);
    const xMin = cx - halfW;
    const xMax = cx + halfW;
    const yMin = cy - halfH;
    const yMax = cy + halfH;

    const gridXStart = Math.floor(xMin / step) * step;
    const gridXEnd = Math.ceil(xMax / step) * step;
    const gridYStart = Math.floor(yMin / step) * step;
    const gridYEnd = Math.ceil(yMax / step) * step;

    // Minor grid lines
    ctx.strokeStyle = "rgba(150, 150, 150, 0.06)";
    ctx.lineWidth = 1;
    for (let x = gridXStart; x <= gridXEnd; x += step) {
        const [sx] = toScreen(x, 0);
        ctx.beginPath();
        ctx.moveTo(sx, 0);
        ctx.lineTo(sx, height);
        ctx.stroke();
    }
    for (let y = gridYStart; y <= gridYEnd; y += step) {
        const [, sy] = toScreen(0, y);
        ctx.beginPath();
        ctx.moveTo(0, sy);
        ctx.lineTo(width, sy);
        ctx.stroke();
    }

    // Axes (if visible)
    ctx.strokeStyle = "rgba(150, 150, 150, 0.15)";
    ctx.lineWidth = 1.5;
    const [axisX] = toScreen(0, 0);
    const [, axisY] = toScreen(0, 0);
    if (axisX > 0 && axisX < width) {
        ctx.beginPath();
        ctx.moveTo(axisX, 0);
        ctx.lineTo(axisX, height);
        ctx.stroke();
    }
    if (axisY > 0 && axisY < height) {
        ctx.beginPath();
        ctx.moveTo(0, axisY);
        ctx.lineTo(width, axisY);
        ctx.stroke();
    }
}

function drawFrame() {
    if (!ctx) return;
    const data = store.epicycleData;
    const basesData = store.basesData;
    if (!data && !basesData) { drawPlaceholder(); return; }

    ctx.clearRect(0, 0, width, height);
    const { cx, cy, scale } = getPathBounds();

    function toScreen(x: number, y: number): [number, number] {
        return [
            width / 2 + (x - cx) * scale,
            height / 2 - (y - cy) * scale,
        ];
    }

    // Background grid
    drawGrid(toScreen, cx, cy, scale);

    const hasEpicycles = props.activeBases.includes("fourier-epicycles");
    const onlyEpicycles = hasEpicycles && props.activeBases.length === 1;

    if (onlyEpicycles && data) {
        drawEpicycleFrame(data, toScreen, scale);
    } else {
        drawMultiBasesFrame(toScreen, scale);
    }
}

function drawEpicycleFrame(
    data: typeof store.epicycleData & {},
    toScreen: (x: number, y: number) => [number, number],
    scale: number,
) {
    if (!ctx) return;

    // Draw original path (faint)
    if (showGhost.value) {
        ctx.beginPath();
        ctx.strokeStyle = "rgba(150, 150, 150, 0.25)";
        ctx.lineWidth = 2.5;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        for (let i = 0; i < data.path.x.length; i++) {
            const [sx, sy] = toScreen(data.path.x[i], data.path.y[i]);
            if (i === 0) ctx.moveTo(sx, sy);
            else ctx.lineTo(sx, sy);
        }
        ctx.closePath();
        ctx.stroke();
    }

    const components: BasisComponent[] = data.components;
    const nVis = Math.min(maxCircles.value, components.length);

    // Use ALL components for accurate tip position (trail matches original path)
    const allPositions = fourierPositionsAt(components, anim.t, components.length);
    const tip = allPositions[allPositions.length - 1];

    // Use nVis components for epicycle visualization
    const visPositions = fourierPositionsAt(components, anim.t, nVis);

    // Trail management: rebuild if scrubbing or if t jumped backwards
    const isScrubbing = anim.scrubbing;
    if (isScrubbing || anim.t < lastTrailT - 0.01) {
        trailX.length = 0;
        trailY.length = 0;
        if (precomputedTrailX && precomputedTrailY) {
            // Fast path: slice pre-computed trail
            const endIdx = Math.min(
                Math.ceil(anim.t * TRAIL_RESOLUTION),
                TRAIL_RESOLUTION,
            );
            for (let i = 0; i <= endIdx; i++) {
                trailX.push(precomputedTrailX[i]);
                trailY.push(precomputedTrailY[i]);
            }
        } else {
            // Fallback: compute on the fly (shouldn't normally happen)
            const nTrailPoints = Math.max(2, Math.ceil(anim.t * 600));
            for (let i = 0; i <= nTrailPoints; i++) {
                const tEval = (i / nTrailPoints) * anim.t;
                const [re, im] = evaluateFourier(components, tEval);
                trailX.push(re);
                trailY.push(im);
            }
        }
    } else {
        trailX.push(tip[0]);
        trailY.push(tip[1]);
    }
    lastTrailT = anim.t;

    // Draw trail (thick, smooth)
    if (trailX.length > 1) {
        ctx.beginPath();
        ctx.strokeStyle = "#ff3412";
        ctx.lineWidth = 3.5;
        ctx.globalAlpha = 0.9;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        const [sx0, sy0] = toScreen(trailX[0], trailY[0]);
        ctx.moveTo(sx0, sy0);
        for (let i = 1; i < trailX.length; i++) {
            const [sx, sy] = toScreen(trailX[i], trailY[i]);
            ctx.lineTo(sx, sy);
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
    }

    // Draw epicycles — use stable bbox for consistent placement
    {
        const isDesktop = width >= 768;
        const hoverT = (currentEpicycleScale - BASE_EPICYCLE_SCALE) / (HOVER_EPICYCLE_SCALE - BASE_EPICYCLE_SCALE);
        const epicycleAlpha = 0.65 + 0.35 * Math.max(0, Math.min(1, hoverT));

        // Use stable (time-invariant) bounding box so epicycles don't shift/resize during animation
        if (!stableEpicycleBbox) {
            stableEpicycleBbox = computeStableEpicycleBbox(components, nVis, toScreen, scale);
        }

        const fit = isDesktop && nVis > 0
            ? computeEpicycleFit(stableEpicycleBbox.minX, stableEpicycleBbox.minY, stableEpicycleBbox.maxX, stableEpicycleBbox.maxY)
            : null;

        // Transform: map raw point (rx, ry) → screen (targetCX + (rx - bboxCX) * fitScale, ...)
        ctx.save();
        if (fit) {
            ctx.translate(fit.targetCX, fit.targetCY);
            ctx.scale(fit.fitScale, fit.fitScale);
            ctx.translate(-fit.bboxCX, -fit.bboxCY);
        }

        // Pass 2: draw circles and arms
        for (let i = 0; i < nVis; i++) {
            const [ccx, ccy] = toScreen(visPositions[i][0], visPositions[i][1]);
            const [tx, ty] = toScreen(visPositions[i + 1][0], visPositions[i + 1][1]);
            const r = components[i].amplitude * scale;
            const color = spectrumColor(i, nVis);

            // Circle
            ctx.beginPath();
            ctx.arc(ccx, ccy, r, 0, Math.PI * 2);
            ctx.strokeStyle = color;
            ctx.globalAlpha = 0.5 * epicycleAlpha;
            ctx.lineWidth = 4;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";
            ctx.stroke();
            ctx.globalAlpha = 1;

            // Arm
            ctx.beginPath();
            ctx.moveTo(ccx, ccy);
            ctx.lineTo(tx, ty);
            ctx.strokeStyle = color;
            ctx.globalAlpha = 0.75 * epicycleAlpha;
            ctx.lineWidth = 3.5;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            ctx.stroke();
            ctx.globalAlpha = 1;

            // Center dot
            ctx.beginPath();
            ctx.arc(ccx, ccy, Math.max(r * 0.1, 5.5), 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.75 * epicycleAlpha;
            ctx.fill();
            ctx.globalAlpha = 1;

            // Endpoint dot
            ctx.beginPath();
            ctx.arc(tx, ty, Math.max(r * 0.08, 4.5), 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.6 * epicycleAlpha;
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        ctx.restore();

        // Update screen-space bounds for hover detection
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

        // Connecting line from epicycle tip to trace position
        if (fit) {
            const visTip = visPositions[visPositions.length - 1];
            const [rawX, rawY] = toScreen(visTip[0], visTip[1]);

            const tipSx = fit.targetCX + (rawX - fit.bboxCX) * fit.fitScale;
            const tipSy = fit.targetCY + (rawY - fit.bboxCY) * fit.fitScale;
            const [traceSx, traceSy] = toScreen(tip[0], tip[1]);

            ctx.beginPath();
            ctx.moveTo(tipSx, tipSy);
            ctx.lineTo(traceSx, traceSy);
            ctx.strokeStyle = "rgba(255, 52, 18, 0.25)";
            ctx.globalAlpha = epicycleAlpha;
            ctx.lineWidth = 1.5;
            ctx.lineCap = "round";
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.globalAlpha = 1;
        }
    }

    // Tip dot on trace
    const [traceSx, traceSy] = toScreen(tip[0], tip[1]);
    ctx.beginPath();
    ctx.arc(traceSx, traceSy, 7, 0, Math.PI * 2);
    ctx.fillStyle = "#ff3412";
    ctx.fill();
    // Glow
    ctx.beginPath();
    ctx.arc(traceSx, traceSy, 15, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 52, 18, 0.15)";
    ctx.fill();

    // Label: t value in top-right
    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#ff3412";
    ctx.globalAlpha = 0.9;
    ctx.font = "bold 16px 'Fira Code', monospace";
    const epicLabel = " Epicycles";
    const eLabelW = ctx.measureText(epicLabel).width;
    ctx.fillText(epicLabel, width - 16, 16);
    ctx.font = "bold 22px 'Computer Modern Serif', Georgia, serif";
    ctx.fillText("\u2131", width - 16 - eLabelW, 14);
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(150, 150, 150, 0.7)";
    ctx.font = "bold 16px 'Fira Code', monospace";
    ctx.fillText(`t = ${anim.t.toFixed(2)}`, width - 16, 40);
}

function drawMultiBasesFrame(
    toScreen: (x: number, y: number) => [number, number],
    scale: number,
) {
    if (!ctx) return;
    const basesData = store.basesData;
    const epicycleData = store.epicycleData;

    // Draw original path (faint)
    if (showGhost.value) {
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
            ctx.beginPath();
            ctx.strokeStyle = "rgba(150, 150, 150, 0.2)";
            ctx.lineWidth = 2;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";
            for (let i = 0; i < origX.length; i++) {
                const [sx, sy] = toScreen(origX[i], origY[i]);
                if (i === 0) ctx.moveTo(sx, sy);
                else ctx.lineTo(sx, sy);
            }
            ctx.stroke();
        }
    }

    // Determine the current level with smooth interpolation
    let level = 1;
    let levelFrac = 0; // interpolation fraction between level and next level
    let levelNext = 1;
    if (basesData && basesData.levels.length > 0) {
        const levels = basesData.levels;
        const pos = anim.t * (levels.length - 1);
        const lo = Math.floor(pos);
        const hi = Math.min(lo + 1, levels.length - 1);
        levelFrac = easeInOutCubic(pos - lo);
        level = levels[lo];
        levelNext = levels[hi];
    } else if (epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        level = Math.max(1, Math.ceil(anim.t * components.length));
        levelNext = level;
    }

    const clipMinX = -width;
    const clipMaxX = 2 * width;
    const clipMinY = -height;
    const clipMaxY = 2 * height;

    // Draw each active basis curve
    for (const basisKey of props.activeBases) {
        const basisName = basisKey.startsWith("fourier") ? "fourier" : basisKey;
        const cfg = basisConfig[basisName];
        if (!cfg) continue;

        const isHovered = hoveredBasis === basisKey;
        // Shimmer: modulate gold brightness with time
        const shimmer = isHovered ? 0.85 + 0.15 * Math.sin(performance.now() / 200) : 0;
        const goldColor = isHovered ? `rgba(240, 182, 50, ${shimmer})` : cfg.color;
        ctx.beginPath();
        ctx.strokeStyle = isHovered ? "#f0b632" : cfg.color;
        ctx.lineWidth = isHovered ? 4 : 3;
        ctx.globalAlpha = isHovered ? shimmer : 0.85;
        if (isHovered) {
            ctx.shadowColor = `rgba(240, 182, 50, ${shimmer * 0.4})`;
            ctx.shadowBlur = 6;
        }
        ctx.lineJoin = "round";
        ctx.lineCap = "round";

        // Look up partial sum data for current and next level
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
                const [sx, sy] = toScreen(px, py);
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
                const [sx, sy] = toScreen(re, im);
                if (i === 0) ctx.moveTo(sx, sy);
                else ctx.lineTo(sx, sy);
            }
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.shadowColor = "transparent";
        ctx.shadowBlur = 0;
    }

    // Epicycle trail + tip + hover overlay when fourier-epicycles is active in multi-basis mode
    const hasEpicyclesMode = props.activeBases.includes("fourier-epicycles");
    if (hasEpicyclesMode && epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        const nVis = Math.min(maxCircles.value, components.length);
        const allPositions = fourierPositionsAt(components, anim.t, components.length);
        const tip = allPositions[allPositions.length - 1];

        // Trail management: rebuild if scrubbing or jumped backwards
        const isScrubbing = anim.scrubbing;
        if (isScrubbing || anim.t < lastTrailT - 0.01) {
            trailX.length = 0;
            trailY.length = 0;
            if (precomputedTrailX && precomputedTrailY) {
                // Fast path: slice pre-computed trail
                const endIdx = Math.min(
                    Math.ceil(anim.t * TRAIL_RESOLUTION),
                    TRAIL_RESOLUTION,
                );
                for (let i = 0; i <= endIdx; i++) {
                    trailX.push(precomputedTrailX[i]);
                    trailY.push(precomputedTrailY[i]);
                }
            } else {
                // Fallback: compute on the fly (shouldn't normally happen)
                const nTrailPoints = Math.max(2, Math.ceil(anim.t * 600));
                for (let i = 0; i <= nTrailPoints; i++) {
                    const tEval = (i / nTrailPoints) * anim.t;
                    const [re, im] = evaluateFourier(components, tEval);
                    trailX.push(re);
                    trailY.push(im);
                }
            }
        } else {
            trailX.push(tip[0]);
            trailY.push(tip[1]);
        }
        lastTrailT = anim.t;

        // Draw trail
        if (trailX.length > 1) {
            ctx.beginPath();
            ctx.strokeStyle = "#ff3412";
            ctx.lineWidth = 3.5;
            ctx.globalAlpha = 0.9;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";
            const [sx0, sy0] = toScreen(trailX[0], trailY[0]);
            ctx.moveTo(sx0, sy0);
            for (let i = 1; i < trailX.length; i++) {
                const [sx, sy] = toScreen(trailX[i], trailY[i]);
                ctx.lineTo(sx, sy);
            }
            ctx.stroke();
            ctx.globalAlpha = 1;
        }

        // Tip dot
        const [traceSx, traceSy] = toScreen(tip[0], tip[1]);
        ctx.beginPath();
        ctx.arc(traceSx, traceSy, 7, 0, Math.PI * 2);
        ctx.fillStyle = "#ff3412";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(traceSx, traceSy, 15, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 52, 18, 0.15)";
        ctx.fill();

        // Epicycle circles/arms overlay — bbox-aware bottom-left placement
        {
            const visPositions = fourierPositionsAt(components, anim.t, nVis);
            const isDesktop = width >= 768;
            const hoverT = (currentEpicycleScale - BASE_EPICYCLE_SCALE) / (HOVER_EPICYCLE_SCALE - BASE_EPICYCLE_SCALE);
            const epicycleAlpha = 0.65 + 0.35 * Math.max(0, Math.min(1, hoverT));

            // Use stable (time-invariant) bounding box
            if (!stableEpicycleBbox) {
                stableEpicycleBbox = computeStableEpicycleBbox(components, nVis, toScreen, scale);
            }

            const fit2 = isDesktop && nVis > 0
                ? computeEpicycleFit(stableEpicycleBbox.minX, stableEpicycleBbox.minY, stableEpicycleBbox.maxX, stableEpicycleBbox.maxY)
                : null;

            ctx.save();
            if (fit2) {
                ctx.translate(fit2.targetCX, fit2.targetCY);
                ctx.scale(fit2.fitScale, fit2.fitScale);
                ctx.translate(-fit2.bboxCX, -fit2.bboxCY);
            }

            // Pass 2: draw
            for (let i = 0; i < nVis; i++) {
                const [ccx, ccy] = toScreen(visPositions[i][0], visPositions[i][1]);
                const [tx, ty] = toScreen(visPositions[i + 1][0], visPositions[i + 1][1]);
                const r = components[i].amplitude * scale;
                const color = spectrumColor(i, nVis);

                ctx.beginPath();
                ctx.arc(ccx, ccy, r, 0, Math.PI * 2);
                ctx.strokeStyle = color;
                ctx.globalAlpha = 0.5 * epicycleAlpha;
                ctx.lineWidth = 5;
                ctx.lineJoin = "round";
                ctx.lineCap = "round";
                ctx.stroke();
                ctx.globalAlpha = 1;

                ctx.beginPath();
                ctx.moveTo(ccx, ccy);
                ctx.lineTo(tx, ty);
                ctx.strokeStyle = color;
                ctx.globalAlpha = 0.75 * epicycleAlpha;
                ctx.lineWidth = 4.5;
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.stroke();
                ctx.globalAlpha = 1;

                ctx.beginPath();
                ctx.arc(ccx, ccy, Math.max(r * 0.1, 5.5), 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.75 * epicycleAlpha;
                ctx.fill();
                ctx.globalAlpha = 1;

                ctx.beginPath();
                ctx.arc(tx, ty, Math.max(r * 0.08, 4.5), 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.6 * epicycleAlpha;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            ctx.restore();

            // Update screen-space epicycle bounds
            if (fit2) {
                epicycleBounds = {
                    x: fit2.targetCX - fit2.scaledW / 2,
                    y: fit2.targetCY - fit2.scaledH / 2,
                    w: fit2.scaledW,
                    h: fit2.scaledH,
                };
            }

            // Connecting line from epicycle tip to trace position
            if (fit2) {
                const visTip = visPositions[visPositions.length - 1];
                const [rawX, rawY] = toScreen(visTip[0], visTip[1]);
                const tipSx = fit2.targetCX + (rawX - fit2.bboxCX) * fit2.fitScale;
                const tipSy = fit2.targetCY + (rawY - fit2.bboxCY) * fit2.fitScale;

                ctx.beginPath();
                ctx.moveTo(tipSx, tipSy);
                ctx.lineTo(traceSx, traceSy);
                ctx.strokeStyle = "rgba(255, 52, 18, 0.25)";
                ctx.globalAlpha = epicycleAlpha;
                ctx.lineWidth = 1.5;
                ctx.lineCap = "round";
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.globalAlpha = 1;
            }
        }
    }

    // Labels in top-right corner
    labelHitRegions = [];
    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    let yOff = 16;
    for (const basisKey of props.activeBases) {
        const basisName = basisKey.startsWith("fourier") ? "fourier" : basisKey;
        const cfg = basisConfig[basisName];
        if (!cfg) continue;
        const modeLabel = basisKey === "fourier-epicycles" ? "Epicycles"
            : basisKey === "fourier-series" ? "Series"
            : cfg.label;
        const isHovered = hoveredBasis === basisKey;
        const labelShimmer = isHovered ? 0.85 + 0.15 * Math.sin(performance.now() / 200) : 0;
        ctx.fillStyle = isHovered ? "#f0b632" : cfg.color;
        ctx.globalAlpha = isHovered ? labelShimmer : 0.9;
        if (isHovered) {
            ctx.shadowColor = `rgba(240, 182, 50, ${labelShimmer * 0.35})`;
            ctx.shadowBlur = 5;
        }
        // Draw mode label
        ctx.font = "bold 16px 'Fira Code', monospace";
        const labelW = ctx.measureText(` ${modeLabel}`).width;
        ctx.fillText(` ${modeLabel}`, width - 16, yOff);
        // Draw icon larger
        ctx.font = "bold 22px 'Computer Modern Serif', Georgia, serif";
        const iconW = ctx.measureText(cfg.icon).width;
        ctx.fillText(cfg.icon, width - 16 - labelW, yOff - 2);
        ctx.shadowColor = "transparent";
        ctx.shadowBlur = 0;
        // Store hit region
        const totalW = iconW + labelW;
        labelHitRegions.push({ key: basisKey, x: width - 16 - totalW, y: yOff - 4, w: totalW + 8, h: 26 });
        yOff += 24;
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(150, 150, 150, 0.7)";
    ctx.font = "bold 16px 'Fira Code', monospace";
    ctx.fillText(`N = ${level}`, width - 16, yOff);
}

function drawPlaceholder() {
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);

    // Subtle grid
    ctx.strokeStyle = "rgba(150, 150, 150, 0.07)";
    ctx.lineWidth = 1;
    const step = 40;
    for (let x = step; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    for (let y = step; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Dashed rounded rect in center
    const boxW = Math.min(280, width * 0.6);
    const boxH = 100;
    const bx = (width - boxW) / 2;
    const by = (height - boxH) / 2;
    const r = 12;
    ctx.beginPath();
    ctx.roundRect(bx, by, boxW, boxH, r);
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = "rgba(150, 150, 150, 0.25)";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.setLineDash([]);

    // Upload arrow icon (simple)
    const cx = width / 2;
    const cy = height / 2 - 12;
    ctx.strokeStyle = "rgba(150, 150, 150, 0.4)";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(cx, cy - 10);
    ctx.lineTo(cx, cy + 10);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - 7, cy - 3);
    ctx.lineTo(cx, cy - 10);
    ctx.lineTo(cx + 7, cy - 3);
    ctx.stroke();

    // Text
    ctx.fillStyle = "rgba(150, 150, 150, 0.6)";
    ctx.font = "500 15px 'Fira Code', monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const msg = store.hasImage ? "Computing..." : "Drag & drop an image here";
    ctx.fillText(msg, cx, height / 2 + 18);
}

watch(
    () => anim.t,
    () => {
        if (!ctx || width === 0) return;
        drawFrame();
    },
);

watch(
    () => store.epicycleData,
    () => {
        trailX.length = 0;
        trailY.length = 0;
        lastTrailT = -1;
        stableEpicycleBbox = null; // Invalidate on data change
        baseFitCenter = null;
        // Pre-compute trail for fast scrubbing
        if (store.epicycleData) {
            precomputeTrail(store.epicycleData.components);
        } else {
            precomputedTrailX = null;
            precomputedTrailY = null;
        }
        if (!ctx || width === 0) {
            setupCanvas();
        } else {
            drawFrame();
        }
    },
);

watch(
    () => props.activeBases,
    () => {
        trailX.length = 0;
        trailY.length = 0;
        lastTrailT = -1;
        if (ctx && width > 0) drawFrame();
    },
    { deep: true },
);

watch(
    () => store.basesData,
    () => {
        if (ctx && width > 0) drawFrame();
    },
);

onMounted(() => {
    setupCanvas();
    resizeObserver = new ResizeObserver(() => setupCanvas());
    if (containerRef.value) resizeObserver.observe(containerRef.value);
});

onUnmounted(() => {
    resizeObserver?.disconnect();
    if (hoverAnimFrame) cancelAnimationFrame(hoverAnimFrame);
    stopShimmer();
});

function exportFrame(options: Record<string, boolean> = {}) {
    if (!canvasRef.value || !ctx) return;

    const {
        withEpicycles: showEpicycles = true,
        withTrail: showTrail = true,
        withGrid: showGrid = true,
        withLabels: showLabels = true,
    } = options;

    // Create an offscreen canvas at the same resolution
    const offCanvas = document.createElement("canvas");
    offCanvas.width = canvasRef.value.width;
    offCanvas.height = canvasRef.value.height;
    const offCtx = offCanvas.getContext("2d")!;
    offCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Temporarily swap ctx to render into offscreen canvas
    const origCtx = ctx;
    const origEpicycleScale = currentEpicycleScale;
    ctx = offCtx;

    // Override rendering flags via temporary state
    if (!showEpicycles) currentEpicycleScale = 0;

    // Render
    const data = store.epicycleData;
    const basesData = store.basesData;
    if (data || basesData) {
        ctx.clearRect(0, 0, width, height);
        const { cx, cy, scale } = getPathBounds();
        function toScreen(x: number, y: number): [number, number] {
            return [width / 2 + (x - cx) * scale, height / 2 - (y - cy) * scale];
        }
        if (showGrid) drawGrid(toScreen, cx, cy, scale);

        const hasEpic = props.activeBases.includes("fourier-epicycles");
        const onlyEpic = hasEpic && props.activeBases.length === 1;

        if (onlyEpic && data) {
            // Selective epicycle render
            drawEpicycleFrame(data, toScreen, scale);
        } else {
            drawMultiBasesFrame(toScreen, scale);
        }

        // Optionally remove labels by clearing the label region
        if (!showLabels) {
            ctx.clearRect(width - 200, 0, 200, 100);
        }
    }

    // Restore
    ctx = origCtx;
    currentEpicycleScale = origEpicycleScale;

    const dataUrl = offCanvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `fourier-frame-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

defineExpose({ anim, exportFrame, showGhost });
</script>

<template>
    <div
        ref="containerRef"
        class="canvas-container"
        @mousemove="onCanvasMouseMove"
        @mouseleave="onCanvasMouseLeave"
    >
        <canvas ref="canvasRef" class="canvas-el" />
    </div>
</template>

<style scoped>
.canvas-container {
    position: relative;
    overflow: hidden;
    border-radius: 0.75rem;
    border: 2px solid hsl(var(--foreground) / 0.15);
    background: hsl(var(--card));
    flex: 1;
    min-height: 0;
    box-shadow: 3px 3px 0px 0px hsl(var(--foreground) / 0.08);
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

:where(.dark) .canvas-container {
    border-color: hsl(var(--foreground) / 0.12);
    box-shadow: 3px 3px 0px 0px hsl(var(--foreground) / 0.06);
}

.canvas-container:hover {
    border-color: hsl(var(--foreground) / 0.25);
    box-shadow: 4px 4px 0px 0px hsl(var(--foreground) / 0.1);
}

:where(.dark) .canvas-container:hover {
    border-color: hsl(var(--foreground) / 0.18);
    box-shadow: 4px 4px 0px 0px hsl(var(--foreground) / 0.08);
}

.canvas-el {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    image-rendering: -webkit-optimize-contrast;
}
</style>

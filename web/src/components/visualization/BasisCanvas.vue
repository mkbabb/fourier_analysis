<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from "vue";
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

let ctx: CanvasRenderingContext2D | null = null;
let width = 0;
let height = 0;
let dpr = 1;
let resizeObserver: ResizeObserver | null = null;

// Mouse tracking for epicycle hover detection
let mouseX = -1;
let mouseY = -1;

// Epicycles always visible at base size, grow on hover
const BASE_EPICYCLE_SCALE = 0.2;
const HOVER_EPICYCLE_SCALE = 0.35;
let currentEpicycleScale = BASE_EPICYCLE_SCALE;
let targetEpicycleScale = BASE_EPICYCLE_SCALE;
let hoverAnimFrame: number | null = null;

// Smoothed epicycle bounding — lerp toward dynamic bounds each frame to prevent jitter
let smoothedFitScale = 0;
let smoothedChainCx = 0;
let smoothedChainCy = 0;
let smoothedInited = false;
const SMOOTH_FACTOR = 0.08; // lower = smoother but slower to track

function spectrumColor(i: number, total: number): string {
    const hue = (1 - i / Math.max(total - 1, 1)) * 300;
    return `hsl(${hue}, 85%, 55%)`;
}

function setupCanvas() {
    if (!canvasRef.value || !containerRef.value) return;
    const rect = containerRef.value.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    dpr = window.devicePixelRatio || 1;
    width = rect.width;
    height = rect.height;

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

function getEpicycleRegion() {
    const isDesktop = width >= 768;

    if (!isDesktop) {
        return { anchorX: 0, anchorY: height, regionScale: 0.3 };
    }

    const s = currentEpicycleScale;
    // Anchor point: bottom-left corner with padding
    const pad = 16;
    return {
        anchorX: pad,
        anchorY: height - pad,
        regionScale: s,
    };
}

function isMouseInEpicycleRegion(): boolean {
    if (mouseX < 0 || mouseY < 0) return false;
    return mouseX < width * 0.4 && mouseY > height * 0.6;
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
}

function onCanvasMouseLeave() {
    mouseX = -1;
    mouseY = -1;
    if (targetEpicycleScale !== BASE_EPICYCLE_SCALE) {
        targetEpicycleScale = BASE_EPICYCLE_SCALE;
        if (!hoverAnimFrame) hoverAnimFrame = requestAnimationFrame(updateHoverScale);
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

    // Trail management
    if (anim.t < lastTrailT - 0.01) {
        trailX.length = 0;
        trailY.length = 0;
    }

    const components: BasisComponent[] = data.components;
    const nVis = Math.min(maxCircles.value, components.length);

    // Use ALL components for accurate tip position (trail matches original path)
    const allPositions = fourierPositionsAt(components, anim.t, components.length);
    const tip = allPositions[allPositions.length - 1];

    // Use nVis components for epicycle visualization
    const visPositions = fourierPositionsAt(components, anim.t, nVis);

    trailX.push(tip[0]);
    trailY.push(tip[1]);
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

    // Draw epicycles — always visible, more defined on hover
    {
        const { anchorX, anchorY, regionScale } = getEpicycleRegion();
        const isDesktop = width >= 768;
        // Alpha: 0.5 at base scale, 1.0 at hover scale
        const hoverT = (currentEpicycleScale - BASE_EPICYCLE_SCALE) / (HOVER_EPICYCLE_SCALE - BASE_EPICYCLE_SCALE);
        const epicycleAlpha = 0.5 + 0.5 * Math.max(0, Math.min(1, hoverT));

        // Dynamic bounding box of the epicycle chain in screen space
        let chainMinX = Infinity, chainMaxX = -Infinity;
        let chainMinY = Infinity, chainMaxY = -Infinity;
        for (let i = 0; i <= nVis; i++) {
            const [sx, sy] = toScreen(visPositions[i][0], visPositions[i][1]);
            // Include the radius of each circle in the bounds
            const r = i < nVis ? components[i].amplitude * scale : 0;
            chainMinX = Math.min(chainMinX, sx - r);
            chainMaxX = Math.max(chainMaxX, sx + r);
            chainMinY = Math.min(chainMinY, sy - r);
            chainMaxY = Math.max(chainMaxY, sy + r);
        }
        const chainW = Math.max(chainMaxX - chainMinX, 1);
        const chainH = Math.max(chainMaxY - chainMinY, 1);
        const chainCxNow = (chainMinX + chainMaxX) / 2;
        const chainCyNow = (chainMinY + chainMaxY) / 2;

        // Compute raw fit scale for this frame
        const targetW = width * regionScale;
        const targetH = height * regionScale;
        const rawFitScale = Math.min(targetW / chainW, targetH / chainH, 1.0);

        // Smooth the values to prevent jitter as phases rotate
        if (!smoothedInited) {
            smoothedFitScale = rawFitScale;
            smoothedChainCx = chainCxNow;
            smoothedChainCy = chainCyNow;
            smoothedInited = true;
        } else {
            smoothedFitScale += (rawFitScale - smoothedFitScale) * SMOOTH_FACTOR;
            smoothedChainCx += (chainCxNow - smoothedChainCx) * SMOOTH_FACTOR;
            smoothedChainCy += (chainCyNow - smoothedChainCy) * SMOOTH_FACTOR;
        }

        const fitScale = smoothedFitScale;
        const chainCx = smoothedChainCx;
        const chainCy = smoothedChainCy;

        ctx.save();
        if (isDesktop) {
            const scaledW = chainW * fitScale;
            const scaledH = chainH * fitScale;
            // Position in bottom-left corner
            const destCx = anchorX + scaledW / 2;
            const destCy = anchorY - scaledH / 2;
            ctx.translate(destCx, destCy);
            ctx.scale(fitScale, fitScale);
            ctx.translate(-chainCx, -chainCy);
        }

        // Draw circles and arms (with fade based on hover)
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
            ctx.arc(ccx, ccy, Math.max(r * 0.08, 4.5), 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.75 * epicycleAlpha;
            ctx.fill();
            ctx.globalAlpha = 1;

            // Endpoint dot
            ctx.beginPath();
            ctx.arc(tx, ty, Math.max(r * 0.06, 3.5), 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.6 * epicycleAlpha;
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        ctx.restore();

        // Connecting line from epicycle tip to trace position
        if (isDesktop) {
            const visTip = visPositions[visPositions.length - 1];
            const [rawX, rawY] = toScreen(visTip[0], visTip[1]);

            const scaledW2 = chainW * fitScale;
            const scaledH2 = chainH * fitScale;
            const destCx2 = anchorX + scaledW2 / 2;
            const destCy2 = anchorY - scaledH2 / 2;

            const tipSx = destCx2 + (rawX - chainCx) * fitScale;
            const tipSy = destCy2 + (rawY - chainCy) * fitScale;
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
}

function drawMultiBasesFrame(
    toScreen: (x: number, y: number) => [number, number],
    scale: number,
) {
    if (!ctx) return;
    const basesData = store.basesData;
    const epicycleData = store.epicycleData;

    // Draw original path (faint)
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

    // Determine the current level
    let level = 1;
    if (basesData && basesData.levels.length > 0) {
        const levels = basesData.levels;
        const levelIdx = Math.max(0, Math.min(levels.length - 1, Math.floor(anim.t * levels.length)));
        level = levels[levelIdx];
    } else if (epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        level = Math.max(1, Math.ceil(anim.t * components.length));
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

        ctx.beginPath();
        ctx.strokeStyle = cfg.color;
        ctx.lineWidth = 3;
        ctx.globalAlpha = 0.85;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";

        if (basisName === "fourier") {
            // Prefer precomputed Fourier partial sums
            const fourierSums = basesData?.partial_sums?.fourier;
            const sumData = (fourierSums as any)?.[level] ?? (fourierSums as any)?.[String(level)];
            if (sumData) {
                for (let i = 0; i < sumData.x.length; i++) {
                    const [sx, sy] = toScreen(sumData.x[i], sumData.y[i]);
                    if (i === 0) ctx.moveTo(sx, sy);
                    else ctx.lineTo(sx, sy);
                }
            } else if (epicycleData) {
                // Fallback: client-side evaluation
                const components: BasisComponent[] = epicycleData.components;
                const nTerms = Math.min(level, components.length);
                const nEval = 500;
                for (let i = 0; i <= nEval; i++) {
                    const tEval = i / nEval;
                    const [re, im] = evaluateFourier(components, tEval, nTerms);
                    const [sx, sy] = toScreen(re, im);
                    if (i === 0) ctx.moveTo(sx, sy);
                    else ctx.lineTo(sx, sy);
                }
            }
        } else {
            // Polynomial bases: clip extreme values to prevent wild diagonal lines (Runge phenomenon)
            const sumData = (basesData?.partial_sums[basisName] as any)?.[level] ?? (basesData?.partial_sums[basisName] as any)?.[String(level)];
            if (sumData) {
                let needsMove = true;
                for (let i = 0; i < sumData.x.length; i++) {
                    const [sx, sy] = toScreen(sumData.x[i], sumData.y[i]);
                    if (sx < clipMinX || sx > clipMaxX || sy < clipMinY || sy > clipMaxY) {
                        needsMove = true;
                        continue;
                    }
                    if (needsMove) {
                        ctx.moveTo(sx, sy);
                        needsMove = false;
                    } else {
                        ctx.lineTo(sx, sy);
                    }
                }
            }
        }
        ctx.stroke();
        ctx.globalAlpha = 1;
    }

    // Epicycle trail + tip + hover overlay when fourier-epicycles is active in multi-basis mode
    const hasEpicyclesMode = props.activeBases.includes("fourier-epicycles");
    if (hasEpicyclesMode && epicycleData) {
        const components: BasisComponent[] = epicycleData.components;
        const nVis = Math.min(maxCircles.value, components.length);
        const allPositions = fourierPositionsAt(components, anim.t, components.length);
        const tip = allPositions[allPositions.length - 1];

        // Trail management
        if (anim.t < lastTrailT - 0.01) {
            trailX.length = 0;
            trailY.length = 0;
        }
        trailX.push(tip[0]);
        trailY.push(tip[1]);
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

        // Epicycle circles/arms overlay — always visible
        {
            const visPositions = fourierPositionsAt(components, anim.t, nVis);
            const { anchorX, anchorY, regionScale } = getEpicycleRegion();
            const isDesktop = width >= 768;
            const hoverT = (currentEpicycleScale - BASE_EPICYCLE_SCALE) / (HOVER_EPICYCLE_SCALE - BASE_EPICYCLE_SCALE);
            const epicycleAlpha = 0.5 + 0.5 * Math.max(0, Math.min(1, hoverT));

            // Dynamic bounding box of the epicycle chain
            let chainMinX2 = Infinity, chainMaxX2 = -Infinity;
            let chainMinY2 = Infinity, chainMaxY2 = -Infinity;
            for (let i = 0; i <= nVis; i++) {
                const [sx, sy] = toScreen(visPositions[i][0], visPositions[i][1]);
                const r = i < nVis ? components[i].amplitude * scale : 0;
                chainMinX2 = Math.min(chainMinX2, sx - r);
                chainMaxX2 = Math.max(chainMaxX2, sx + r);
                chainMinY2 = Math.min(chainMinY2, sy - r);
                chainMaxY2 = Math.max(chainMaxY2, sy + r);
            }
            const chainW2 = Math.max(chainMaxX2 - chainMinX2, 1);
            const chainH2 = Math.max(chainMaxY2 - chainMinY2, 1);
            const chainCxNow2 = (chainMinX2 + chainMaxX2) / 2;
            const chainCyNow2 = (chainMinY2 + chainMaxY2) / 2;

            const targetW = width * regionScale;
            const targetH = height * regionScale;
            const rawFitScale2 = Math.min(targetW / chainW2, targetH / chainH2, 1.0);

            if (!smoothedInited) {
                smoothedFitScale = rawFitScale2;
                smoothedChainCx = chainCxNow2;
                smoothedChainCy = chainCyNow2;
                smoothedInited = true;
            } else {
                smoothedFitScale += (rawFitScale2 - smoothedFitScale) * SMOOTH_FACTOR;
                smoothedChainCx += (chainCxNow2 - smoothedChainCx) * SMOOTH_FACTOR;
                smoothedChainCy += (chainCyNow2 - smoothedChainCy) * SMOOTH_FACTOR;
            }

            const fitScale = smoothedFitScale;
            const chainCx2 = smoothedChainCx;
            const chainCy2 = smoothedChainCy;

            ctx.save();
            if (isDesktop) {
                const scaledW = chainW2 * fitScale;
                const scaledH = chainH2 * fitScale;
                const destCx = anchorX + scaledW / 2;
                const destCy = anchorY - scaledH / 2;
                ctx.translate(destCx, destCy);
                ctx.scale(fitScale, fitScale);
                ctx.translate(-chainCx2, -chainCy2);
            }

            for (let i = 0; i < nVis; i++) {
                const [ccx, ccy] = toScreen(visPositions[i][0], visPositions[i][1]);
                const [tx, ty] = toScreen(visPositions[i + 1][0], visPositions[i + 1][1]);
                const r = components[i].amplitude * scale;
                const color = spectrumColor(i, nVis);

                ctx.beginPath();
                ctx.arc(ccx, ccy, r, 0, Math.PI * 2);
                ctx.strokeStyle = color;
                ctx.globalAlpha = 0.5 * epicycleAlpha;
                ctx.lineWidth = 4;
                ctx.lineJoin = "round";
                ctx.lineCap = "round";
                ctx.stroke();
                ctx.globalAlpha = 1;

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

                ctx.beginPath();
                ctx.arc(ccx, ccy, Math.max(r * 0.08, 4.5), 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.75 * epicycleAlpha;
                ctx.fill();
                ctx.globalAlpha = 1;

                ctx.beginPath();
                ctx.arc(tx, ty, Math.max(r * 0.06, 3.5), 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.6 * epicycleAlpha;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            ctx.restore();

            if (isDesktop) {
                const visTip = visPositions[visPositions.length - 1];
                const [rawX, rawY] = toScreen(visTip[0], visTip[1]);
                const scaledW2 = chainW2 * fitScale;
                const scaledH2 = chainH2 * fitScale;
                const destCx2 = anchorX + scaledW2 / 2;
                const destCy2 = anchorY - scaledH2 / 2;
                const tipSx = destCx2 + (rawX - chainCx2) * fitScale;
                const tipSy = destCy2 + (rawY - chainCy2) * fitScale;

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
    ctx.font = "bold 13px 'Fira Code', monospace";
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
        ctx.fillStyle = cfg.color;
        ctx.globalAlpha = 0.9;
        ctx.fillText(`${cfg.icon} ${modeLabel}`, width - 16, yOff);
        yOff += 20;
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(150, 150, 150, 0.7)";
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

    ctx.fillStyle = "#999";
    ctx.font = "500 14px 'Fira Code', monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(
        store.hasImage ? "Click compute to begin" : "Upload an image to begin",
        width / 2,
        height / 2,
    );
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
        smoothedInited = false;
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

defineExpose({ anim, exportFrame });
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

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";
import { useSessionStore } from "@/stores/session";
import { useAnimationStore } from "@/stores/animation";
import { fourierPositionsAt } from "@/lib/bases";
import type { BasisComponent } from "@/lib/types";

const store = useSessionStore();
const anim = useAnimationStore();
const canvasRef = ref<HTMLCanvasElement>();
const containerRef = ref<HTMLDivElement>();

const maxCircles = ref(80);

let ctx: CanvasRenderingContext2D | null = null;
let width = 0;
let height = 0;
let resizeObserver: ResizeObserver | null = null;

function spectrumColor(i: number, total: number): string {
    const hue = (1 - i / Math.max(total - 1, 1)) * 300;
    return `hsl(${hue}, 85%, 55%)`;
}

function setupCanvas() {
    if (!canvasRef.value || !containerRef.value) return;
    const rect = containerRef.value.getBoundingClientRect();
    if (rect.width === 0) return; // Not laid out yet
    const dpr = window.devicePixelRatio || 1;
    const size = Math.min(rect.width, 800);
    width = size;
    height = size;
    canvasRef.value.width = size * dpr;
    canvasRef.value.height = size * dpr;
    canvasRef.value.style.width = `${size}px`;
    canvasRef.value.style.height = `${size}px`;
    ctx = canvasRef.value.getContext("2d")!;
    ctx.scale(dpr, dpr);

    // After setup, draw the appropriate frame
    if (store.epicycleData) {
        drawFrame();
    } else {
        drawPlaceholder();
    }
}

/* Offset epicycles to bottom-left on desktop (wide viewports) */
function getViewBounds() {
    const data = store.epicycleData;
    if (!data) return { cx: 0, cy: 0, scale: 1 };

    const xs = data.path.x;
    const ys = data.path.y;
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

    const dataCx = (minX + maxX) / 2;
    const dataCy = (minY + maxY) / 2;

    // On wide viewports, offset center toward top-right so drawing sits bottom-left
    const isDesktop = width >= 500;
    const offsetX = isDesktop ? rangeX * 0.12 : 0;
    const offsetY = isDesktop ? -rangeY * 0.10 : 0;

    return {
        cx: dataCx + offsetX,
        cy: dataCy + offsetY,
        scale,
    };
}

const trailX: number[] = [];
const trailY: number[] = [];
let lastTrailT = -1;

function drawFrame() {
    if (!ctx) return;
    const data = store.epicycleData;
    if (!data) {
        drawPlaceholder();
        return;
    }

    ctx.clearRect(0, 0, width, height);
    const { cx, cy, scale } = getViewBounds();

    function toScreen(x: number, y: number): [number, number] {
        return [
            width / 2 + (x - cx) * scale,
            height / 2 - (y - cy) * scale,
        ];
    }

    // Draw original path (faint but bolder)
    ctx.beginPath();
    ctx.strokeStyle = "rgba(150, 150, 150, 0.3)";
    ctx.lineWidth = 1.5;
    for (let i = 0; i < data.path.x.length; i++) {
        const [sx, sy] = toScreen(data.path.x[i], data.path.y[i]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
    }
    ctx.stroke();

    // Get epicycle positions
    const components: BasisComponent[] = data.components;
    const nVis = Math.min(maxCircles.value, components.length);
    const positions = fourierPositionsAt(components, anim.t, nVis);

    // Draw circles and arms — bolder strokes
    for (let i = 0; i < nVis; i++) {
        const [ccx, ccy] = toScreen(positions[i][0], positions[i][1]);
        const [tx, ty] = toScreen(positions[i + 1][0], positions[i + 1][1]);
        const r = components[i].amplitude * scale;
        const color = spectrumColor(i, nVis);

        // Circle
        ctx.beginPath();
        ctx.arc(ccx, ccy, r, 0, Math.PI * 2);
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.45;
        ctx.lineWidth = 1.8;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Arm
        ctx.beginPath();
        ctx.moveTo(ccx, ccy);
        ctx.lineTo(tx, ty);
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.6;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Center dot
        ctx.beginPath();
        ctx.arc(ccx, ccy, Math.max(r * 0.04, 1.5), 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.6;
        ctx.fill();
        ctx.globalAlpha = 1;
    }

    // Trail
    if (anim.t < lastTrailT) {
        trailX.length = 0;
        trailY.length = 0;
    }
    const tip = positions[positions.length - 1];
    trailX.push(tip[0]);
    trailY.push(tip[1]);
    lastTrailT = anim.t;

    if (trailX.length > 1) {
        ctx.beginPath();
        ctx.strokeStyle = "#ff3412";
        ctx.lineWidth = 2.5;
        ctx.globalAlpha = 0.92;
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
    const [tipSx, tipSy] = toScreen(tip[0], tip[1]);
    ctx.beginPath();
    ctx.arc(tipSx, tipSy, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ff3412";
    ctx.fill();
    // Glow
    ctx.beginPath();
    ctx.arc(tipSx, tipSy, 10, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 52, 18, 0.18)";
    ctx.fill();
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
        store.hasImage ? "Click 'Epicycles' to compute" : "Upload an image to begin",
        width / 2,
        height / 2,
    );
}

// keyframes.js drives the animation loop via the store's reactive t
watch(() => anim.t, () => {
    if (!ctx || width === 0) return;
    drawFrame();
});

watch(() => store.epicycleData, () => {
    trailX.length = 0;
    trailY.length = 0;
    lastTrailT = -1;
    drawFrame();
});

onMounted(() => {
    resizeObserver = new ResizeObserver(() => setupCanvas());
    if (containerRef.value) resizeObserver.observe(containerRef.value);
});

onUnmounted(() => {
    resizeObserver?.disconnect();
});

defineExpose({ anim });
</script>

<template>
    <div
        ref="containerRef"
        class="overflow-hidden rounded-xl border border-border bg-card transition-all duration-200 hover:shadow-sm"
        style="aspect-ratio: 1; min-height: 200px"
    >
        <canvas ref="canvasRef" class="block w-full" />
    </div>
</template>

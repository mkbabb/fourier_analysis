<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import type { ContourAsset } from "@/lib/types";
import {
    closedSplinePath,
    nearestSegmentIndex,
    simplifyClosedPoints,
    smoothClosedPoints,
    zipPoints,
    unzipPoints,
    type Point2D,
} from "@/lib/contourEditing";
import { overlayUrl } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspace";
import { useContourHistory } from "./composables/useContourHistory";
import { usePointDrag } from "./composables/usePointDrag";

const props = defineProps<{
    contour: ContourAsset;
    imageSlug: string | null;
    showImageOverlay?: boolean;
}>();

const emit = defineEmits<{
    stateChange: [state: { canUndo: boolean; canRedo: boolean; canDelete: boolean; pointCount: number }];
    save: [points: { x: number[]; y: number[] }];
}>();

const MARGIN = 0.15;

const wStore = useWorkspaceStore();

// State
const points = ref<Point2D[]>([]);
const svgRef = ref<SVGSVGElement | null>(null);

// Magnet mode: drag adjacent points with falloff
const magnetRadius = ref(3); // 0 = off, 1-10 = number of adjacent points affected; default on

// Composables
const { pushHistory, undo, redo, initHistory, canUndo, canRedo } = useContourHistory(points);
const { dragging, selectedIdx, onPointPointerDown: rawPointPointerDown, onPointerMove, onPointerUp, deselect } = usePointDrag(
    points,
    magnetRadius,
    svgPoint,
    pushHistory,
);

// Stable bounds — computed from initial contour, not live points
const stableBounds = ref({ minX: 0, maxX: 1, minY: 0, maxY: 1, width: 1, height: 1 });

// Initialize from contour
function initFromContour() {
    const pts = zipPoints(props.contour.points.x, props.contour.points.y);
    points.value = pts;
    initHistory(pts);
    deselect();

    // Compute stable bounds from initial points
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const p of pts) {
        if (p.x < minX) minX = p.x;
        if (p.x > maxX) maxX = p.x;
        if (p.y < minY) minY = p.y;
        if (p.y > maxY) maxY = p.y;
    }
    stableBounds.value = { minX, maxX, minY, maxY, width: maxX - minX || 1, height: maxY - minY || 1 };

    emitState();
}

watch(() => props.contour, initFromContour, { immediate: true });

// Bounds — use stable bounds for viewBox and image overlay, live bounds for nothing
const bounds = computed(() => stableBounds.value);

const viewBox = computed(() => {
    const b = bounds.value;
    const padX = b.width * MARGIN;
    const padY = b.height * MARGIN;
    return `${b.minX - padX} ${-(b.maxY + padY)} ${b.width + padX * 2} ${b.height + padY * 2}`;
});

// Spline path
const splinePath = computed(() => closedSplinePath(points.value));

// Image overlay: use the resized overlay endpoint + image_bounds for positioning.
// Derive resize from image_bounds so the overlay always matches the extraction dimensions.
const overlayHref = computed(() => {
    if (!props.imageSlug) return null;
    const ib = props.contour.image_bounds;
    const resize = ib
        ? Math.round(Math.max(ib.maxX - ib.minX, ib.maxY - ib.minY))
        : (wStore.contourSettings?.resize ?? 768);
    return overlayUrl(props.imageSlug, resize);
});

// Image bounds from contour document (authoritative data-space rectangle).
const imageOverlayRect = computed(() => {
    const ib = props.contour.image_bounds;
    if (!ib) return null;
    return {
        x: ib.minX,
        y: ib.minY,
        w: ib.maxX - ib.minX,
        h: ib.maxY - ib.minY,
    };
});

// Wrapped undo/redo with side effects
function doUndo() {
    undo();
    deselect();
    emitState();
}

function doRedo() {
    redo();
    deselect();
    emitState();
}

function emitState() {
    emit("stateChange", {
        canUndo: canUndo(),
        canRedo: canRedo(),
        canDelete: selectedIdx.value !== null,
        pointCount: points.value.length,
    });
}

// SVG coordinate conversion
function svgPoint(e: MouseEvent | PointerEvent): Point2D {
    const svg = svgRef.value!;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = svg.getScreenCTM()!.inverse();
    const transformed = pt.matrixTransform(ctm);
    // Y is flipped in our coordinate system
    return { x: transformed.x, y: -transformed.y };
}

// Interaction handlers
function onDblClick(e: MouseEvent) {
    const click = svgPoint(e);
    const idx = nearestSegmentIndex(points.value, click);
    points.value.splice(idx, 0, click);
    selectedIdx.value = idx;
    pushHistory();
    emitState();
}

function onPointPointerDown(idx: number, e: PointerEvent) {
    rawPointPointerDown(idx, e);
    emitState();
}

function onBgClick() {
    deselect();
    emitState();
}

function onKeyDown(e: KeyboardEvent) {
    if ((e.key === "Delete" || e.key === "Backspace") && selectedIdx.value !== null) {
        e.preventDefault();
        deleteSelected();
    }
    if (e.key === "z" && (e.metaKey || e.ctrlKey) && !e.shiftKey) {
        e.preventDefault();
        doUndo();
    }
    if ((e.key === "z" && (e.metaKey || e.ctrlKey) && e.shiftKey) || (e.key === "y" && (e.metaKey || e.ctrlKey))) {
        e.preventDefault();
        doRedo();
    }
}

function deleteSelected() {
    if (selectedIdx.value === null || points.value.length <= 3) return;
    points.value.splice(selectedIdx.value, 1);
    deselect();
    pushHistory();
    emitState();
}

function applySmooth() {
    points.value = smoothClosedPoints(points.value);
    deselect();
    pushHistory();
    emitState();
}

function applySimplify() {
    points.value = simplifyClosedPoints(points.value);
    deselect();
    pushHistory();
    emitState();
}

function resetToExtraction() {
    initFromContour();
}

function getPoints(): { x: number[]; y: number[] } {
    return unzipPoints(points.value);
}

onMounted(() => {
    window.addEventListener("keydown", onKeyDown);
});

onUnmounted(() => {
    window.removeEventListener("keydown", onKeyDown);
});

defineExpose({
    undo: doUndo,
    redo: doRedo,
    applySmooth,
    applySimplify,
    deleteSelected,
    resetToExtraction,
    getPoints,
    points,
    magnetRadius,
});
</script>

<template>
    <div class="editor-shell" tabindex="0">
        <svg
            ref="svgRef"
            :viewBox="viewBox"
            preserveAspectRatio="xMidYMid meet"
            class="editor-svg"
            @dblclick="onDblClick"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
            @pointercancel="onPointerUp"
            @click.self="onBgClick"
        >
            <g transform="scale(1,-1)">
                <!-- Image overlay — positioned using authoritative image_bounds -->
                <image
                    v-if="showImageOverlay && overlayHref && imageOverlayRect"
                    :href="overlayHref"
                    :x="imageOverlayRect.x"
                    :y="imageOverlayRect.y"
                    :width="imageOverlayRect.w"
                    :height="imageOverlayRect.h"
                    :transform="`translate(0, ${imageOverlayRect.y * 2 + imageOverlayRect.h}) scale(1, -1)`"
                    style="opacity: 0.28; pointer-events: none"
                    preserveAspectRatio="xMidYMid meet"
                />

                <!-- Spline path -->
                <path
                    :d="splinePath"
                    fill="none"
                    stroke="hsl(40 90% 55% / 0.85)"
                    stroke-width="3"
                    vector-effect="non-scaling-stroke"
                    class="spline-path"
                />

                <!-- Control points -->
                <circle
                    v-for="(pt, i) in points"
                    :key="i"
                    :cx="pt.x"
                    :cy="pt.y"
                    :r="3.5"
                    vector-effect="non-scaling-stroke"
                    class="control-point"
                    :class="{ selected: i === selectedIdx }"
                    @pointerdown="onPointPointerDown(i, $event)"
                />
            </g>
        </svg>
    </div>
</template>

<style scoped>
.editor-shell {
    flex: 1;
    min-height: 0;
    border-radius: var(--radius);
    border: 1px solid hsl(var(--border));
    overflow: hidden;
    outline: none;
    background:
        linear-gradient(hsl(var(--foreground) / 0.05) 1px, transparent 1px),
        linear-gradient(90deg, hsl(var(--foreground) / 0.05) 1px, transparent 1px),
        hsl(var(--card));
    background-size: 28px 28px, 28px 28px, auto;
}

.editor-svg {
    width: 100%;
    height: 100%;
    display: block;
    cursor: crosshair;
}

.control-point {
    fill: hsl(40 90% 55% / 0.6);
    stroke: hsl(40 90% 55%);
    stroke-width: 2.5;
    cursor: grab;
    transition: fill 0.15s, r 0.15s;
}

.control-point:hover {
    fill: hsl(40 90% 55% / 0.5);
}

.spline-path {
    filter: drop-shadow(0 0 2px hsl(40 90% 55% / 0.3));
    transition: filter 0.2s ease;
}

.editor-svg:hover .spline-path {
    animation: golden-shimmer 1.2s ease-in-out infinite;
}

@keyframes golden-shimmer {
    0%, 100% { filter: drop-shadow(0 0 2px hsl(40 90% 55% / 0.3)); }
    50% { filter: drop-shadow(0 0 5px hsl(40 90% 55% / 0.5)); }
}

.control-point.selected {
    fill: hsl(40 90% 55%);
    stroke: hsl(var(--background));
}

.control-point:active {
    cursor: grabbing;
}
</style>

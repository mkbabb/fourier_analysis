<template>
    <div class="cartoon-card levels-card">
        <h3 class="card-title">Harmonic Levels</h3>

        <div class="levels-controls">
            <div class="level-row">
                <label class="level-label">Low</label>
                <input
                    type="number"
                    :value="lowLevel"
                    @change="emitLow(($event.target as HTMLInputElement).value)"
                    min="1"
                    :max="highLevel - 1"
                    step="1"
                    class="level-input fira-code"
                />
                <input
                    type="range"
                    :value="lowLevel"
                    @input="emitLow(($event.target as HTMLInputElement).value)"
                    min="1"
                    :max="highLevel - 1"
                    step="1"
                    class="styled-slider"
                    :style="sliderStyle(lowLevel, 1, highLevel - 1, VIZ_COLORS.chebyshev)"
                />
            </div>

            <div class="level-row">
                <label class="level-label">High</label>
                <input
                    type="number"
                    :value="highLevel"
                    @change="emitHigh(($event.target as HTMLInputElement).value)"
                    :min="lowLevel + 1"
                    max="100"
                    step="1"
                    class="level-input fira-code"
                />
                <input
                    type="range"
                    :value="highLevel"
                    @input="emitHigh(($event.target as HTMLInputElement).value)"
                    :min="lowLevel + 1"
                    max="100"
                    step="1"
                    class="styled-slider"
                    :style="sliderStyle(highLevel, lowLevel + 1, 100, VIZ_COLORS.chebyshev)"
                />
            </div>
        </div>

        <div class="grid">
            <button
                v-for="level in levels"
                :key="level"
                class="grid-cell"
                :class="{
                    active: level === activeLevel,
                    'is-bound': level === lowLevel || level === highLevel,
                }"
                @click="$emit('select', level)"
            >
                <svg viewBox="0 0 200 200" class="grid-svg">
                    <path
                        :d="getPath(level)"
                        fill="none"
                        stroke="hsl(var(--accent-red))"
                        stroke-width="4"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                </svg>
                <span
                    class="grid-label"
                    :class="{ 'grid-label-active': level === activeLevel }"
                >
                    n={{ level }}
                </span>
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { sliderStyle } from "@/composables/useMorphConfig";
import { VIZ_COLORS } from "@/lib/colors";
import type { FourierShape } from "@/lib/svg-fourier";
import { interpolateAtHarmonicLevel, pointsToSvgPath } from "@/lib/svg-fourier";

const props = defineProps<{
    shape: FourierShape;
    levels: number[];
    activeLevel: number;
    lowLevel: number;
    highLevel: number;
}>();

const emit = defineEmits<{
    "update:lowLevel": [value: number];
    "update:highLevel": [value: number];
    select: [level: number];
}>();

function emitLow(raw: string) {
    const v = Math.max(1, Math.min(props.highLevel - 1, Number(raw) || 1));
    emit("update:lowLevel", v);
}

function emitHigh(raw: string) {
    const v = Math.max(props.lowLevel + 1, Math.min(100, Number(raw) || 1));
    emit("update:highLevel", v);
}

function getPath(level: number): string {
    const points = interpolateAtHarmonicLevel(props.shape, level);
    return pointsToSvgPath(points);
}
</script>

<style scoped>
.levels-card {
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}

.card-title {
    font-family: var(--font-serif);
    font-size: 1rem;
    font-weight: 400;
    color: hsl(var(--foreground));
    margin-bottom: 0.75rem;
}

/* ── Level controls ──────────────────────────── */

.levels-controls {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}

.level-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.level-label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    white-space: nowrap;
    min-width: 2.5rem;
}

.level-input {
    width: 3.5rem;
    padding: 0.125rem 0.375rem;
    border: 1.5px solid hsl(var(--foreground) / 0.15);
    border-radius: 0.375rem;
    background: hsl(var(--background));
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
    font-weight: 600;
    text-align: center;
    outline: none;
    flex-shrink: 0;
    transition: border-color 0.15s ease;
    -moz-appearance: textfield;
}

.level-input::-webkit-inner-spin-button,
.level-input::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

.level-input:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.15);
}

/* HarmonicLevelGrid slider overrides — slightly smaller thumb */
.styled-slider {
    flex: 1;
}

.styled-slider::-webkit-slider-thumb {
    width: 20px;
    height: 20px;
}

.styled-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
}

/* ── Preview grid ────────────────────────────── */

.grid {
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: 0.375rem;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
}

.grid-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
    padding: 0.375rem;
    border: 1.5px solid hsl(var(--foreground) / 0.12);
    border-radius: 0.5rem;
    background: hsl(var(--card));
    cursor: pointer;
    flex-shrink: 0;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
}

.grid-cell:hover {
    border-color: hsl(var(--accent-red) / 0.5);
    transform: scale(1.04);
}

.grid-cell:active {
    transform: scale(0.96);
}

.grid-cell.active {
    border-color: hsl(var(--accent-red));
    box-shadow: 0 0 0 2px hsl(var(--accent-red) / 0.15);
}

.grid-cell.is-bound {
    border-color: #60a5fa;
    box-shadow: 0 0 0 1.5px rgba(96, 165, 250, 0.2);
}

.grid-svg {
    width: 64px;
    height: 64px;
    overflow: visible;
}

.grid-label {
    font-family: var(--font-mono);
    font-size: 0.625rem;
    color: hsl(var(--muted-foreground));
    transition: color 0.15s;
}

.grid-label-active {
    color: hsl(var(--accent-red));
    font-weight: 600;
}

</style>

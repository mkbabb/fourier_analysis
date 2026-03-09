/**
 * Composable for animated Fourier morphing between two shapes.
 *
 * Animation phases:
 * 1. settle-out:  Current shape degrades from full harmonics → low harmonics
 * 2. morph:       Cross-fade point arrays from shape A (low) → shape B (low)
 * 3. settle-in:   New shape resolves from low harmonics → full harmonics
 *
 * All transitions are driven by keyframes.js Animation instances
 * with easing functions (from value.js) applied to the interpolation t.
 */

import { ref, computed, onUnmounted, type Ref } from "vue";
import { Animation } from "@mkbabb/keyframes.js";
import { timingFunctions } from "@mkbabb/value.js";
import type { FourierShape } from "@/lib/svg-fourier";
import {
    interpolateAtHarmonicLevel,
    lerpPoints,
    pointsToSvgPath,
} from "@/lib/svg-fourier";

export type MorphPhase = "idle" | "settle-out" | "morph" | "settle-in";

// ── Easing presets ──────────────────────────────────────────────────

export type EasingFn = (t: number) => number;

/** Display labels for easing preset names. */
const EASING_LABELS: Record<string, string> = {
    linear: "Linear",
    "ease-in": "Ease In",
    "ease-out": "Ease Out",
    "ease-in-out": "Ease In-Out",
    "ease-in-back": "Back In",
    "ease-out-back": "Back Out",
    "ease-in-out-back": "Back In-Out",
    "ease-in-quad": "Ease In Quad",
    "ease-out-quad": "Ease Out Quad",
    "ease-in-out-quad": "Ease In-Out Quad",
    "ease-in-cubic": "Ease In Cubic",
    "ease-out-cubic": "Ease Out Cubic",
    "ease-in-out-cubic": "Ease In-Out Cubic",
    "ease-in-sine": "Ease In Sine",
    "ease-out-sine": "Ease Out Sine",
    "ease-in-out-sine": "Ease In-Out Sine",
    "ease-in-expo": "Ease In Expo",
    "ease-out-expo": "Ease Out Expo",
    "ease-in-out-expo": "Ease In-Out Expo",
    "ease-in-circ": "Ease In Circ",
    "ease-out-circ": "Ease Out Circ",
    "ease-in-out-circ": "Ease In-Out Circ",
};

export interface EasingPreset {
    label: string;
    fn: EasingFn;
}

/** All available easing presets, backed by value.js timing functions. */
export const EASING_PRESETS: Record<string, EasingPreset> = Object.fromEntries(
    Object.entries(EASING_LABELS).map(([name, label]) => [
        name,
        { label, fn: timingFunctions[name as keyof typeof timingFunctions] as EasingFn },
    ]),
);

export const EASING_PRESET_NAMES = Object.keys(EASING_PRESETS);

// ── Config type ─────────────────────────────────────────────────────

export interface MorphConfig {
    settleOutMs: number;
    morphMs: number;
    settleInMs: number;
    lowLevel: number;
    highLevel: number;
    settleOutEasing: string;
    morphEasing: string;
    settleInEasing: string;
}

export const DEFAULT_MORPH_CONFIG: MorphConfig = {
    settleOutMs: 150,
    morphMs: 50,
    settleInMs: 150,
    lowLevel: 5,
    highLevel: 35,
    settleOutEasing: "linear",
    morphEasing: "linear",
    settleInEasing: "linear",
};

function getEasingFn(name: string): EasingFn {
    return EASING_PRESETS[name]?.fn ?? EASING_PRESETS.linear.fn;
}

// ── Composable ──────────────────────────────────────────────────────

export interface UseFourierMorphOptions {
    config?: MorphConfig;
}

export function useFourierMorph(options: UseFourierMorphOptions = {}) {
    const config = ref<MorphConfig>({ ...(options.config ?? DEFAULT_MORPH_CONFIG) });

    const phase: Ref<MorphPhase> = ref("idle");
    const currentPoints: Ref<[number, number][]> = ref([]);
    const currentPath = computed(() => pointsToSvgPath(currentPoints.value));
    const harmonicLevel = ref(config.value.highLevel);
    /** 0 = fully "from" shape, 1 = fully "to" shape. Updated during morphTo(). */
    const morphProgress = ref(0);

    let activeShape: FourierShape | null = null;
    let currentAnim: Animation | null = null;

    function setShape(shape: FourierShape) {
        stopAnim();
        activeShape = shape;
        harmonicLevel.value = config.value.highLevel;
        currentPoints.value = interpolateAtHarmonicLevel(shape, config.value.highLevel);
        phase.value = "idle";
    }

    /** Set the displayed harmonic level without animation. */
    function setLevel(shape: FourierShape, level: number) {
        stopAnim();
        activeShape = shape;
        harmonicLevel.value = level;
        currentPoints.value = interpolateAtHarmonicLevel(shape, level);
        phase.value = "idle";
    }

    function updateConfig(newConfig: Partial<MorphConfig>) {
        Object.assign(config.value, newConfig);
    }

    function getIdlePoints(): [number, number][] {
        if (!activeShape) return [];
        return interpolateAtHarmonicLevel(activeShape, config.value.highLevel);
    }

    function stopAnim() {
        if (currentAnim) {
            currentAnim.stop();
            currentAnim = null;
        }
    }

    function createTweenAnimation(
        durationMs: number,
        onTick: (t: number) => void,
    ): Animation {
        const a = new Animation({
            duration: durationMs,
            iterationCount: 1,
            timingFunction: "linear",
            fillMode: "forwards",
            useWAAPI: false,
        });

        a.addFrame("0%", { v: "0px" }, (_vars: any, time: number) => {
            const t = Math.min(time / a.options.duration, 1);
            onTick(t);
        });
        a.addFrame("100%", { v: "1px" });
        a.parse();

        return a;
    }

    async function morphTo(from: FourierShape, to: FourierShape): Promise<void> {
        stopAnim();

        const {
            settleOutMs,
            morphMs,
            settleInMs,
            lowLevel,
            highLevel,
            settleOutEasing,
            morphEasing,
            settleInEasing,
        } = config.value;

        const easeOut = getEasingFn(settleOutEasing);
        const easeMorph = getEasingFn(morphEasing);
        const easeIn = getEasingFn(settleInEasing);

        const totalMs = settleOutMs + morphMs + settleInMs;

        // Phase 1: Settle out
        phase.value = "settle-out";
        await new Promise<void>((resolve) => {
            currentAnim = createTweenAnimation(settleOutMs, (tRaw: number) => {
                const t = easeOut(tRaw);
                const level = highLevel + (lowLevel - highLevel) * t;
                harmonicLevel.value = level;
                currentPoints.value = interpolateAtHarmonicLevel(from, Math.max(lowLevel, level));
                morphProgress.value = (tRaw * settleOutMs) / totalMs;
            });
            currentAnim.play().then(() => resolve());
        });

        // Phase 2: Morph
        phase.value = "morph";
        const fromLowPoints = interpolateAtHarmonicLevel(from, lowLevel);
        const toLowPoints = interpolateAtHarmonicLevel(to, lowLevel);

        await new Promise<void>((resolve) => {
            currentAnim = createTweenAnimation(morphMs, (tRaw: number) => {
                const t = easeMorph(tRaw);
                currentPoints.value = lerpPoints(fromLowPoints, toLowPoints, t);
                morphProgress.value = (settleOutMs + tRaw * morphMs) / totalMs;
            });
            currentAnim.play().then(() => resolve());
        });

        // Phase 3: Settle in
        phase.value = "settle-in";
        activeShape = to;

        await new Promise<void>((resolve) => {
            currentAnim = createTweenAnimation(settleInMs, (tRaw: number) => {
                const t = easeIn(tRaw);
                const level = lowLevel + (highLevel - lowLevel) * t;
                harmonicLevel.value = level;
                currentPoints.value = interpolateAtHarmonicLevel(to, Math.min(highLevel, level));
                morphProgress.value = (settleOutMs + morphMs + tRaw * settleInMs) / totalMs;
            });
            currentAnim.play().then(() => resolve());
        });

        phase.value = "idle";
        morphProgress.value = 1;
        currentAnim = null;
    }

    onUnmounted(() => stopAnim());

    return {
        phase,
        config,
        currentPath,
        currentPoints,
        harmonicLevel,
        morphProgress,
        setShape,
        setLevel,
        updateConfig,
        getIdlePoints,
        morphTo,
    };
}

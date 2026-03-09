/**
 * Composable for managing Fourier morph configuration state.
 *
 * Provides reactive config, serialization to JSON, reset to defaults,
 * and syncing with a useFourierMorph instance.
 */

import { reactive, ref, computed, watch, onUnmounted } from "vue";
import {
    DEFAULT_MORPH_CONFIG,
    EASING_PRESETS,
    EASING_PRESET_NAMES,
    type MorphConfig,
} from "@/composables/useFourierMorph";

export { EASING_PRESETS, EASING_PRESET_NAMES, DEFAULT_MORPH_CONFIG };
export type { MorphConfig };

/**
 * Generate an SVG path `d` string for an easing curve preview.
 * Draws the easing function as a polyline in a 40×20 viewBox.
 */
export function easingCurvePath(name: string): string {
    const fn = EASING_PRESETS[name]?.fn ?? ((t: number) => t);
    const steps = 24;
    let d = "";
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const v = fn(t);
        const x = 2 + t * 36;
        const y = 18 - v * 16;
        d += i === 0 ? `M${x},${y}` : ` L${x},${y}`;
    }
    return d;
}

/**
 * Compute slider CSS custom properties for the styled-slider pattern.
 */
export function sliderStyle(
    value: number,
    min: number,
    max: number,
    color: string,
): Record<string, string> {
    const progress = ((value - min) / (max - min)) * 100;
    return {
        "--progress": progress + "%",
        "--slider-color": color,
    };
}

/**
 * Generate a nice spread of preview levels from 1 to highLevel,
 * including the low and high bookends.
 */
export function computePreviewLevels(lowLevel: number, highLevel: number): number[] {
    const levels = new Set<number>();

    const candidates = [1, 2, 3, 5, 8, 12, 18, 25, 35, 50, 75, 100];
    for (const c of candidates) {
        levels.add(c);
    }

    if (lowLevel > 1) levels.add(lowLevel);
    levels.add(highLevel);

    return Array.from(levels).sort((a, b) => a - b);
}

export function useMorphConfig(initialConfig?: Partial<MorphConfig>) {
    const config = reactive<MorphConfig>({
        ...DEFAULT_MORPH_CONFIG,
        ...initialConfig,
    });

    const totalMs = computed(
        () => config.settleOutMs + config.morphMs + config.settleInMs,
    );

    const previewLevels = computed(() =>
        computePreviewLevels(config.lowLevel, config.highLevel),
    );

    const copied = ref(false);
    let copiedTimer: ReturnType<typeof setTimeout> | null = null;

    onUnmounted(() => {
        if (copiedTimer) clearTimeout(copiedTimer);
    });

    function reset() {
        Object.assign(config, DEFAULT_MORPH_CONFIG);
    }

    function updateField(field: keyof MorphConfig, event: Event) {
        const target = event.target as HTMLInputElement;
        (config as any)[field] = Number(target.value);
    }

    function toJSON(): string {
        return JSON.stringify(config, null, 2);
    }

    function copyToClipboard() {
        navigator.clipboard.writeText(toJSON()).then(() => {
            copied.value = true;
            if (copiedTimer) clearTimeout(copiedTimer);
            copiedTimer = setTimeout(() => (copied.value = false), 2000);
        });
    }

    /** Create a watcher that syncs config changes into a morph composable. */
    function syncWith(morph: { updateConfig: (cfg: Partial<MorphConfig>) => void }) {
        watch(
            () => ({ ...config }),
            (cfg) => morph.updateConfig(cfg),
            { deep: true },
        );
    }

    return {
        config,
        totalMs,
        previewLevels,
        copied,
        reset,
        updateField,
        toJSON,
        copyToClipboard,
        syncWith,
    };
}

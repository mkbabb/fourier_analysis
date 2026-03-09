<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Collapsible } from "@/components/ui/collapsible";
import { Tooltip } from "@/components/ui/tooltip";

const basisDisplay: Record<string, { icon: string; label: string; color: string }> = {
    fourier: { icon: "\u2131", label: "Fourier", color: "#ff3412" },
    chebyshev: { icon: "T\u2099", label: "Chebyshev", color: "#3b82f6" },
    legendre: { icon: "P\u2099", label: "Legendre", color: "#a855f7" },
};

const fourierModes = ["fourier-epicycles", "fourier-series"] as const;

const props = defineProps<{
    activeBases?: string[];
    nHarmonics?: number;
    nPoints?: number;
}>();

const emit = defineEmits<{
    (e: "update:activeBases", bases: string[]): void;
    (e: "update:nHarmonics", v: number): void;
    (e: "update:nPoints", v: number): void;
}>();

const harmonicsProgress = computed(() => (((props.nHarmonics ?? 200) - 1) / 499) * 100);
const pointsProgress = computed(() => (((props.nPoints ?? 1024) - 128) / (4096 - 128)) * 100);

const selected = ref<string[]>(props.activeBases ?? ["fourier-epicycles"]);

watch(() => props.activeBases, (v) => { if (v) selected.value = [...v]; });

const fourierMode = computed(() => {
    if (selected.value.includes("fourier-epicycles")) return "fourier-epicycles";
    if (selected.value.includes("fourier-series")) return "fourier-series";
    return null;
});

const fourierLabel = computed(() => {
    if (fourierMode.value === "fourier-epicycles") return "Epicycles";
    if (fourierMode.value === "fourier-series") return "Series";
    return "Fourier";
});

function isBasisActive(key: string): boolean {
    if (key === "fourier") return fourierMode.value !== null;
    return selected.value.includes(key);
}

function getBasisLabel(key: string, info: { label: string }): string {
    if (key === "fourier") return fourierLabel.value;
    return info.label;
}

const basisTooltips: Record<string, string> = {
    fourier: "Fourier series — click to cycle: epicycles \u2192 series \u2192 off",
    chebyshev: "Chebyshev polynomial approximation",
    legendre: "Legendre polynomial approximation",
};

function getBasisTooltip(key: string): string {
    return basisTooltips[key] ?? key;
}

function toggleBasis(key: string) {
    if (key === "fourier") {
        // Cycle: epicycles -> series -> off -> epicycles
        const hasEpi = selected.value.includes("fourier-epicycles");
        const hasSeries = selected.value.includes("fourier-series");
        const otherBases = selected.value.filter(b => !b.startsWith("fourier"));
        selected.value = [...otherBases];
        if (hasEpi) {
            selected.value.push("fourier-series");
        } else if (hasSeries) {
            // Go to "off" only if other bases keep the selection non-empty
            if (otherBases.length === 0) {
                // Can't be empty — cycle back to epicycles
                selected.value.push("fourier-epicycles");
            }
            // else: fourier is off, other bases remain
        } else {
            selected.value.push("fourier-epicycles");
        }
    } else {
        const idx = selected.value.indexOf(key);
        if (idx >= 0) {
            if (selected.value.length <= 1) return;
            selected.value.splice(idx, 1);
        } else {
            selected.value.push(key);
        }
    }
    emit("update:activeBases", [...selected.value]);
}
</script>

<template>
    <div class="cartoon-card p-3">
        <Collapsible title="Basis" subtitle="decomposition & resolution" :default-open="true">
            <div class="flex gap-1.5 pt-1 pb-1">
                <Tooltip v-for="(info, key) in basisDisplay" :key="key" :text="getBasisTooltip(key as string)">
                    <button
                        class="basis-pill"
                        :class="{ active: isBasisActive(key as string) }"
                        :style="isBasisActive(key as string) ? { '--pill-color': info.color } : {}"
                        @click="toggleBasis(key as string)"
                    >
                        <span class="basis-icon cm-serif font-semibold">{{ info.icon }}</span>
                        {{ getBasisLabel(key as string, info) }}
                    </button>
                </Tooltip>
            </div>

            <div class="space-y-3 pt-2">
                <!-- Harmonics -->
                <div>
                    <label class="mb-1.5 flex items-center justify-between text-sm font-medium text-muted-foreground">
                        <span>Harmonics (N)</span>
                        <span class="fira-code text-foreground">{{ nHarmonics }}</span>
                    </label>
                    <input
                        :value="nHarmonics"
                        @input="emit('update:nHarmonics', parseInt(($event.target as HTMLInputElement).value))"
                        type="range"
                        min="1"
                        max="500"
                        step="1"
                        class="styled-slider w-full"
                        :style="{ '--progress': harmonicsProgress + '%', '--slider-color': '#ff3412' }"
                    />
                </div>

                <!-- Sample Points -->
                <div>
                    <label class="mb-1.5 flex items-center justify-between text-sm font-medium text-muted-foreground">
                        <span>Sample Points</span>
                        <span class="fira-code text-foreground">{{ nPoints }}</span>
                    </label>
                    <input
                        :value="nPoints"
                        @input="emit('update:nPoints', parseInt(($event.target as HTMLInputElement).value))"
                        type="range"
                        min="128"
                        max="4096"
                        step="128"
                        class="styled-slider w-full"
                        :style="{ '--progress': pointsProgress + '%', '--slider-color': '#3b82f6' }"
                    />
                </div>
            </div>
        </Collapsible>
    </div>
</template>

<style scoped>
/* Gradient sliders */
.styled-slider {
    -webkit-appearance: none;
    appearance: none;
    height: 12px;
    border-radius: 6px;
    touch-action: none;
    background: linear-gradient(
        to right,
        var(--slider-color) var(--progress),
        hsl(var(--secondary)) var(--progress)
    );
    outline: none;
    cursor: pointer;
}

.styled-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--slider-color);
    cursor: pointer;
    border: 2.5px solid hsl(var(--background));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275),
                box-shadow 0.15s ease;
}

.styled-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.styled-slider::-webkit-slider-thumb:active {
    transform: scale(0.95);
}

.styled-slider::-moz-range-thumb {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--slider-color);
    cursor: pointer;
    border: 2.5px solid hsl(var(--background));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.styled-slider::-moz-range-progress {
    background: var(--slider-color);
    border-radius: 6px;
    height: 12px;
}

.styled-slider::-moz-range-track {
    background: hsl(var(--secondary));
    border-radius: 6px;
    height: 12px;
}

.basis-icon {
    display: inline-flex;
    align-items: center;
    font-size: 1.5em;
    line-height: 1;
    min-width: 1.2em;
    justify-content: center;
}
.basis-pill {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.35rem 0.625rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 2px solid hsl(var(--foreground) / 0.12);
    background: transparent;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
}
.basis-pill:hover {
    border-color: hsl(var(--foreground) / 0.25);
}
.basis-pill.active {
    background: color-mix(in srgb, var(--pill-color) 12%, transparent);
    border-color: color-mix(in srgb, var(--pill-color) 40%, transparent);
    color: var(--pill-color);
}
</style>

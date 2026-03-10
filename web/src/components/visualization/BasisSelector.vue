<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Collapsible } from "@/components/ui/collapsible";
import { Tooltip } from "@/components/ui/tooltip";
import { VIZ_COLORS } from "@/lib/colors";
import { basisDisplay } from "./lib/basis-display";
import { RotateCcw } from "lucide-vue-next";

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

const harmonicsProgress = computed(() => (((props.nHarmonics ?? 50) - 1) / 499) * 100);
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

const DEFAULTS = {
    activeBases: ["fourier-epicycles"],
    nHarmonics: 50,
    nPoints: 1024,
} as const;

const isDefault = computed(() =>
    (props.nHarmonics ?? 50) === DEFAULTS.nHarmonics
    && (props.nPoints ?? 1024) === DEFAULTS.nPoints
    && selected.value.length === 1
    && selected.value[0] === "fourier-epicycles",
);

function resetDefaults() {
    selected.value = [...DEFAULTS.activeBases];
    emit("update:activeBases", [...DEFAULTS.activeBases]);
    emit("update:nHarmonics", DEFAULTS.nHarmonics);
    emit("update:nPoints", DEFAULTS.nPoints);
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
    <div class="cartoon-card px-3 py-2">
        <Collapsible title="Basis" subtitle="decomposition & resolution" :default-open="true">
            <template #actions>
                <button
                    class="reset-icon-btn"
                    :class="{ 'is-default': isDefault }"
                    title="Reset to defaults"
                    @click.stop="resetDefaults"
                >
                    <RotateCcw class="h-3.5 w-3.5" />
                </button>
            </template>
            <div class="flex flex-wrap justify-center gap-1.5 pt-1 pb-1">
                <Tooltip v-for="(info, key) in basisDisplay" :key="key" :text="getBasisTooltip(key as string)">
                    <button
                        class="basis-pill"
                        :class="{ active: isBasisActive(key as string) }"
                        :style="isBasisActive(key as string) ? { '--pill-color': info.color } : {}"
                        @click="toggleBasis(key as string)"
                    >
                        <span class="basis-icon cm-serif font-semibold" :class="{ 'basis-icon--fourier': key === 'fourier' }">{{ info.icon }}</span>
                        {{ getBasisLabel(key as string, info) }}
                    </button>
                </Tooltip>
            </div>

            <div class="space-y-3 pt-2">
                <!-- Harmonics -->
                <div>
                    <label class="mb-1.5 flex items-center justify-between text-sm font-medium text-muted-foreground">
                        <span>Harmonics (N)</span>
                        <input
                            type="number"
                            class="inline-number fira-code"
                            :value="nHarmonics"
                            min="1"
                            max="500"
                            step="1"
                            @input="emit('update:nHarmonics', Math.max(1, Math.min(500, parseInt(($event.target as HTMLInputElement).value) || 1)))"
                        />
                    </label>
                    <input
                        :value="nHarmonics"
                        @input="emit('update:nHarmonics', parseInt(($event.target as HTMLInputElement).value))"
                        type="range"
                        min="1"
                        max="500"
                        step="1"
                        class="styled-slider w-full"
                        :style="{ '--progress': harmonicsProgress + '%', '--slider-color': VIZ_COLORS.fourier }"
                    />
                </div>

                <!-- Sample Points -->
                <div>
                    <label class="mb-1.5 flex items-center justify-between text-sm font-medium text-muted-foreground">
                        <span>Sample Points</span>
                        <input
                            type="number"
                            class="inline-number fira-code"
                            :value="nPoints"
                            min="128"
                            max="4096"
                            step="128"
                            @input="emit('update:nPoints', Math.max(128, Math.min(4096, parseInt(($event.target as HTMLInputElement).value) || 128)))"
                        />
                    </label>
                    <input
                        :value="nPoints"
                        @input="emit('update:nPoints', parseInt(($event.target as HTMLInputElement).value))"
                        type="range"
                        min="128"
                        max="4096"
                        step="128"
                        class="styled-slider w-full"
                        :style="{ '--progress': pointsProgress + '%', '--slider-color': VIZ_COLORS.chebyshev }"
                    />
                </div>
            </div>
        </Collapsible>
    </div>
</template>

<style scoped>
.inline-number {
    width: 2.75rem;
    text-align: right;
    background: transparent;
    border: none;
    border-bottom: 1px solid transparent;
    color: hsl(var(--foreground));
    font-size: inherit;
    padding: 0;
    outline: none;
    -moz-appearance: textfield;
    transition: border-color 0.15s;
}
.inline-number:hover,
.inline-number:focus {
    border-bottom-color: hsl(var(--foreground) / 0.3);
}
.inline-number::-webkit-inner-spin-button,
.inline-number::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

.basis-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5em;
    line-height: 1;
    min-width: 1.2em;
    height: 1em;
}
.basis-icon--fourier {
    font-size: 2.2em;
    margin: -0.35em -0.1em;
    transform: translateY(0.06em);
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

/* Compact pills on mobile so all three fit on one line */
@media (max-width: 639px) {
    .basis-pill {
        padding: 0.25rem 0.5rem;
        font-size: 0.6875rem;
        gap: 0.125rem;
        border-width: 1.5px;
    }
    .basis-icon {
        font-size: 1.25em;
        min-width: 1em;
    }
    .basis-icon--fourier {
        font-size: 1.75em;
        margin: -0.3em -0.05em;
    }
}
.basis-pill:hover {
    border-color: hsl(var(--foreground) / 0.25);
}
.basis-pill.active {
    background: color-mix(in srgb, var(--pill-color) 12%, transparent);
    border-color: color-mix(in srgb, var(--pill-color) 40%, transparent);
    color: var(--pill-color);
}

.reset-icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.25rem;
    border: none;
    background: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    border-radius: 0.25rem;
    transition: color 0.15s, opacity 0.2s;
}
.reset-icon-btn.is-default {
    opacity: 0.25;
    pointer-events: none;
}
.reset-icon-btn:hover {
    color: hsl(var(--foreground));
}
</style>

<script setup lang="ts">
import { ref } from "vue";
import { useSessionStore } from "@/stores/session";
import { Settings2, Play, Layers, Loader2 } from "lucide-vue-next";

const store = useSessionStore();

const strategy = ref(store.session?.parameters.strategy ?? "auto");
const blurSigma = ref(store.session?.parameters.blur_sigma ?? 1.0);
const nHarmonics = ref(store.session?.parameters.n_harmonics ?? 200);
const nPoints = ref(store.session?.parameters.n_points ?? 1024);

const strategies = [
    { value: "auto", label: "Auto (Multi-threshold)" },
    { value: "threshold", label: "Otsu Threshold" },
    { value: "multi_threshold", label: "Multi-threshold" },
    { value: "canny", label: "Canny Edges" },
];

const computing = ref(false);

async function runCompute() {
    computing.value = true;
    await store.updateSettings({
        parameters: {
            strategy: strategy.value,
            blur_sigma: blurSigma.value,
            n_harmonics: nHarmonics.value,
            n_points: nPoints.value,
        },
    });
    await store.runEpicycles({
        n_harmonics: nHarmonics.value,
        n_points: nPoints.value,
    });
    computing.value = false;
}

async function runBases() {
    computing.value = true;
    await store.runBases({
        max_degree: nHarmonics.value,
        n_points: nPoints.value,
    });
    computing.value = false;
}
</script>

<template>
    <div class="rounded-xl border border-border bg-card p-4 card-hover animate-fade-in">
        <h3 class="fraunces mb-3 text-sm font-semibold tracking-tight flex items-center gap-2">
            <Settings2 class="h-4 w-4 text-muted-foreground" />
            Contour Settings
        </h3>

        <div class="space-y-3.5">
            <!-- Strategy -->
            <div>
                <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Strategy</label>
                <select
                    v-model="strategy"
                    class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors duration-200 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                >
                    <option v-for="s in strategies" :key="s.value" :value="s.value">
                        {{ s.label }}
                    </option>
                </select>
            </div>

            <!-- Blur Sigma -->
            <div>
                <label class="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Blur Sigma</span>
                    <span class="fira-code text-foreground">{{ blurSigma.toFixed(1) }}</span>
                </label>
                <input
                    v-model.number="blurSigma"
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    class="w-full"
                />
            </div>

            <!-- Harmonics -->
            <div>
                <label class="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Harmonics (N)</span>
                    <span class="fira-code text-foreground">{{ nHarmonics }}</span>
                </label>
                <input
                    v-model.number="nHarmonics"
                    type="range"
                    min="1"
                    max="500"
                    step="1"
                    class="w-full"
                />
            </div>

            <!-- Points -->
            <div>
                <label class="mb-1.5 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Sample Points</span>
                    <span class="fira-code text-foreground">{{ nPoints }}</span>
                </label>
                <input
                    v-model.number="nPoints"
                    type="range"
                    min="128"
                    max="4096"
                    step="128"
                    class="w-full"
                />
            </div>

            <!-- Buttons -->
            <div class="flex gap-2 pt-1">
                <button
                    class="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-all duration-200 hover:opacity-90 disabled:opacity-50 btn-press"
                    :disabled="computing || store.loading"
                    @click="runCompute"
                >
                    <Loader2 v-if="computing" class="h-3.5 w-3.5 animate-spin" />
                    <Play v-else class="h-3.5 w-3.5" />
                    {{ computing ? "Computing..." : "Epicycles" }}
                </button>
                <button
                    class="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm font-medium transition-all duration-200 hover:bg-muted disabled:opacity-50 btn-press"
                    :disabled="computing || store.loading"
                    @click="runBases"
                >
                    <Layers class="h-3.5 w-3.5" />
                    All Bases
                </button>
            </div>
        </div>
    </div>
</template>

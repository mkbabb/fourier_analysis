<script setup lang="ts">
import { computed, ref } from "vue";
import { useSessionStore } from "@/stores/session";
import { ChevronDown, ChevronUp } from "lucide-vue-next";
import { Collapsible } from "@/components/ui/collapsible";
import { Tooltip } from "@/components/ui/tooltip";

const store = useSessionStore();
const expanded = ref(false);

const topComponents = computed(() => {
    if (!store.epicycleData) return [];
    return store.epicycleData.components.slice(0, expanded.value ? 40 : 12);
});

const totalComponents = computed(() => store.epicycleData?.components.length ?? 0);

const maxAmplitude = computed(() => {
    if (!topComponents.value.length) return 1;
    return topComponents.value[0].amplitude;
});

function spectrumColor(i: number, total: number): string {
    const hue = (1 - i / Math.max(total - 1, 1)) * 300;
    return `hsl(${hue}, 85%, 55%)`;
}

function formatPhase(phase: number): string {
    return `${(phase * 180 / Math.PI).toFixed(1)}°`;
}

function formatPercent(amplitude: number): string {
    if (!maxAmplitude.value) return "0%";
    return `${((amplitude / maxAmplitude.value) * 100).toFixed(1)}%`;
}
</script>

<template>
    <div class="cartoon-card px-3 py-2">
        <Collapsible title="Coefficients" subtitle="Fourier spectrum" :default-open="false">
            <div class="pt-1">
                <div class="flex items-center justify-end mb-2">
                    <span class="fira-code text-xs text-muted-foreground">
                        {{ topComponents.length }} / {{ totalComponents }}
                    </span>
                </div>

                <div v-if="topComponents.length" class="space-y-1 max-h-[300px] overflow-y-auto">
                    <TransitionGroup name="coeff-list">
                        <div
                            v-for="(comp, i) in topComponents"
                            :key="`${comp.index}-${i}`"
                            class="coeff-row flex items-center gap-2 text-xs group relative"
                        >
                            <span class="w-8 text-right fira-code text-muted-foreground tabular-nums">
                                {{ comp.index >= 0 ? "+" : "" }}{{ comp.index }}
                            </span>
                            <div class="flex-1 h-3 rounded-full bg-muted/50 overflow-hidden">
                                <div
                                    class="h-full rounded-full transition-all duration-500 ease-out"
                                    :style="{
                                        width: `${(comp.amplitude / maxAmplitude) * 100}%`,
                                        backgroundColor: spectrumColor(i, topComponents.length),
                                        minWidth: '2px',
                                    }"
                                />
                            </div>
                            <span class="w-16 text-right fira-code text-muted-foreground tabular-nums">
                                {{ comp.amplitude.toFixed(2) }}
                            </span>
                            <!-- Hover tooltip -->
                            <div class="coeff-tooltip">
                                <div class="flex items-center gap-1.5 mb-1">
                                    <span class="inline-block w-2 h-2 rounded-full" :style="{ backgroundColor: spectrumColor(i, topComponents.length) }" />
                                    <span class="font-semibold">n = {{ comp.index }}</span>
                                </div>
                                <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-[10px]">
                                    <span class="text-muted-foreground">Amplitude</span>
                                    <span class="fira-code">{{ comp.amplitude.toFixed(4) }}</span>
                                    <span class="text-muted-foreground">Phase</span>
                                    <span class="fira-code">{{ formatPhase(comp.phase) }}</span>
                                    <span class="text-muted-foreground">Relative</span>
                                    <span class="fira-code">{{ formatPercent(comp.amplitude) }}</span>
                                    <span class="text-muted-foreground">Re / Im</span>
                                    <span class="fira-code">{{ comp.coefficient[0].toFixed(3) }} / {{ comp.coefficient[1].toFixed(3) }}</span>
                                </div>
                            </div>
                        </div>
                    </TransitionGroup>

                    <Tooltip :text="expanded ? 'Collapse to top 12 coefficients' : `Show top 40 of ${totalComponents} coefficients`">
                        <button
                            v-if="totalComponents > 12"
                            class="mt-2 flex w-full items-center justify-center gap-1 rounded-md py-1.5 text-xs font-medium text-muted-foreground transition-all duration-200 hover:text-foreground hover:bg-muted cursor-pointer"
                            @click="expanded = !expanded"
                        >
                            <component :is="expanded ? ChevronUp : ChevronDown" class="h-3.5 w-3.5" />
                            {{ expanded ? "Show less" : `Show more (${totalComponents} total)` }}
                        </button>
                    </Tooltip>
                </div>

                <p v-else class="text-xs text-muted-foreground py-3 text-center">
                    Compute epicycles to see coefficients
                </p>
            </div>
        </Collapsible>
    </div>
</template>

<style scoped>
.coeff-list-enter-active {
    transition: all 0.3s ease;
}
.coeff-list-leave-active {
    transition: all 0.2s ease;
}
.coeff-list-enter-from {
    opacity: 0;
    transform: translateX(-8px);
}
.coeff-list-leave-to {
    opacity: 0;
    transform: translateX(8px);
}
.coeff-list-move {
    transition: transform 0.3s ease;
}

/* Hover tooltip */
.coeff-row {
    cursor: default;
}
.coeff-tooltip {
    display: none;
    position: absolute;
    left: 0;
    top: calc(100% + 4px);
    z-index: 20;
    background: hsl(var(--popover));
    color: hsl(var(--popover-foreground));
    border: 1.5px solid hsl(var(--border));
    border-radius: 0.5rem;
    padding: 0.5rem 0.625rem;
    font-size: 0.6875rem;
    white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    pointer-events: none;
}
.coeff-row:hover .coeff-tooltip {
    display: block;
}
</style>

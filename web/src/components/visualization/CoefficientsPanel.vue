<script setup lang="ts">
import { computed, ref } from "vue";
import { useSessionStore } from "@/stores/session";
import { BarChart3, ChevronDown, ChevronUp } from "lucide-vue-next";

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
</script>

<template>
    <div class="rounded-xl border border-border bg-card p-4 card-hover animate-fade-in">
        <div class="flex items-center justify-between mb-3">
            <h3 class="fraunces text-sm font-semibold tracking-tight flex items-center gap-2">
                <BarChart3 class="h-4 w-4 text-muted-foreground" />
                Coefficients
            </h3>
            <span class="fira-code text-xs text-muted-foreground">
                {{ topComponents.length }} / {{ totalComponents }}
            </span>
        </div>

        <div v-if="topComponents.length" class="space-y-1">
            <TransitionGroup name="coeff-list">
                <div
                    v-for="(comp, i) in topComponents"
                    :key="`${comp.index}-${i}`"
                    class="flex items-center gap-2 text-xs group"
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
                </div>
            </TransitionGroup>

            <!-- Expand/collapse -->
            <button
                v-if="totalComponents > 12"
                class="mt-2 flex w-full items-center justify-center gap-1 rounded-md py-1.5 text-xs font-medium text-muted-foreground transition-all duration-200 hover:text-foreground hover:bg-muted btn-press"
                @click="expanded = !expanded"
            >
                <component :is="expanded ? ChevronUp : ChevronDown" class="h-3.5 w-3.5" />
                {{ expanded ? "Show less" : `Show more (${totalComponents} total)` }}
            </button>
        </div>

        <p v-else class="text-xs text-muted-foreground py-3 text-center">
            Compute epicycles to see coefficients
        </p>
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
</style>

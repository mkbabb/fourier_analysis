<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { watchDebounced } from "@vueuse/core";
import { useSessionStore } from "@/stores/session";
import { useAnimationStore } from "@/stores/animation";
import { VIZ_COLORS } from "@/lib/colors";
import { Collapsible } from "@/components/ui/collapsible";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
} from "@/components/ui/select";
import { Wand2, ChevronRight } from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from "reka-ui";
import SliderControl from "@/components/ui/SliderControl.vue";

const advancedOpen = ref(false);

const props = defineProps<{
    nHarmonics: number;
    nPoints: number;
}>();

const store = useSessionStore();
const anim = useAnimationStore();

const strategy = ref(store.session?.parameters.strategy ?? "auto");
const blurSigma = ref(store.session?.parameters.blur_sigma ?? 1.0);
const minContourArea = ref((store.session?.parameters.min_contour_area ?? 0) * 100);
const maxContours = ref<number>(store.session?.parameters.max_contours ?? 0);
const smoothContours = ref(store.session?.parameters.smooth_contours ?? 0.1);

const computing = computed({
    get: () => store.computing,
    set: (v: boolean) => { store.computing = v; },
});

const strategyLabels: Record<string, string> = {
    auto: "Auto",
    threshold: "Otsu Threshold",
    multi_threshold: "Multi-threshold",
    canny: "Canny Edges",
};

const strategyDescriptions: Record<string, string> = {
    auto: "Automatically selects the best contour extraction method based on the image",
    threshold: "Otsu's method — optimal single-threshold binary segmentation",
    multi_threshold: "Multiple thresholds for complex images with many intensity levels",
    canny: "Edge detection — best for line drawings and high-contrast boundaries",
};

const strategyLabel = computed(() => strategyLabels[strategy.value] ?? strategy.value);

async function runCompute() {
    if (!store.hasImage || computing.value) return;
    computing.value = true;
    await store.updateSettings({
        parameters: {
            strategy: strategy.value,
            blur_sigma: blurSigma.value,
            min_contour_area: minContourArea.value / 100,
            max_contours: maxContours.value === 0 ? null : maxContours.value,
            smooth_contours: smoothContours.value,
            n_harmonics: props.nHarmonics,
            n_points: props.nPoints,
        },
    });
    const results = await Promise.allSettled([
        store.runEpicycles({
            n_harmonics: props.nHarmonics,
            n_points: props.nPoints,
        }),
        store.runBases({
            max_degree: props.nHarmonics,
            n_points: props.nPoints,
        }),
    ]);
    computing.value = false;
    // Only auto-play if at least one computation succeeded
    const anyOk = results.some((r) => r.status === "fulfilled");
    if (anyOk && (store.epicycleData || store.basesData)) {
        anim.reset();
        anim.play();
    }
}

// Auto-compute on settings change (debounced 800ms)
watchDebounced(
    () => [strategy.value, blurSigma.value, minContourArea.value, maxContours.value, smoothContours.value, props.nHarmonics, props.nPoints],
    () => runCompute(),
    { debounce: 800, immediate: false },
);

// Compute on mount if image exists but no data
onMounted(() => {
    if (store.hasImage && !store.epicycleData && !store.basesData) {
        runCompute();
    }
});
</script>

<template>
    <div class="cartoon-card px-3 py-2">
        <Collapsible title="Contour" subtitle="edge extraction settings" :default-open="false">
            <div class="space-y-3 pt-1">
                <!-- Strategy -->
                <div>
                    <label class="mb-1.5 block text-sm font-medium text-muted-foreground">Strategy</label>
                    <Select v-model="strategy">
                        <SelectTrigger class="w-full h-10 text-sm border-2 border-foreground/15 rounded-lg">
                            <div class="inline-flex items-center gap-1.5">
                                <Wand2 v-if="strategy === 'auto'" class="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                                {{ strategyLabel }}
                            </div>
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem v-for="(desc, key) in strategyDescriptions" :key="key" :value="key">
                                <div>
                                    <div class="font-medium">{{ strategyLabels[key] }}</div>
                                    <div class="text-xs text-muted-foreground max-w-[280px]">{{ desc }}</div>
                                </div>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <!-- Blur Sigma -->
                <Tooltip text="Soften before tracing — crank it up for furry subjects or noisy backgrounds">
                    <SliderControl
                        v-model="blurSigma"
                        label="Blur Sigma"
                        :min="0"
                        :max="5"
                        :step="0.1"
                        :color="VIZ_COLORS.amber"
                        :format-value="(v: number) => v.toFixed(1)"
                    />
                </Tooltip>

                <!-- Advanced divider + collapsible -->
                <CollapsibleRoot v-model:open="advancedOpen">
                    <div class="advanced-divider">
                        <div class="divider-line" />
                        <CollapsibleTrigger class="advanced-trigger">
                            <span>Advanced</span>
                            <ChevronRight class="h-3 w-3 text-muted-foreground/60 transition-transform duration-200" :class="{ 'rotate-90': advancedOpen }" />
                        </CollapsibleTrigger>
                        <div class="divider-line" />
                    </div>

                    <CollapsibleContent class="advanced-content">
                        <div class="advanced-grid">
                            <!-- Min Area % -->
                            <Tooltip text="Ignore tiny contours — raise to drop grass, fences, and stray edges">
                                <SliderControl
                                    v-model="minContourArea"
                                    label="Min Area %"
                                    :min="0"
                                    :max="20"
                                    :step="0.5"
                                    :color="VIZ_COLORS.amber"
                                    :format-value="(v: number) => v.toFixed(1)"
                                />
                            </Tooltip>

                            <!-- Max Contours -->
                            <Tooltip text="How many outlines to keep — 1 for a clean silhouette, more for interior detail">
                                <SliderControl
                                    v-model="maxContours"
                                    label="Max Contours"
                                    :min="0"
                                    :max="50"
                                    :step="1"
                                    :color="VIZ_COLORS.amber"
                                    :format-value="(v: number) => v === 0 ? 'All' : String(v)"
                                />
                            </Tooltip>

                            <!-- Smoothing -->
                            <Tooltip text="Iron out jagged edges — tame fur, leaves, and pixelated boundaries">
                                <SliderControl
                                    v-model="smoothContours"
                                    label="Smoothing"
                                    :min="0"
                                    :max="1"
                                    :step="0.05"
                                    :color="VIZ_COLORS.amber"
                                    :format-value="(v: number) => v.toFixed(2)"
                                />
                            </Tooltip>
                        </div>
                    </CollapsibleContent>
                </CollapsibleRoot>

            </div>
        </Collapsible>

    </div>
</template>

<style scoped>
/* Advanced section */
.advanced-divider {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.25rem;
}
.divider-line {
    flex: 1;
    height: 1px;
    background: hsl(var(--foreground) / 0.1);
}
.advanced-trigger {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
    user-select: none;
    font-size: 0.6875rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    color: hsl(var(--foreground) / 0.4);
    transition: color 0.15s;
    white-space: nowrap;
    padding: 0.125rem 0;
}
.advanced-trigger:hover {
    color: hsl(var(--foreground) / 0.6);
}

.advanced-content {
    overflow: hidden;
}
.advanced-content[data-state="open"] {
    animation: adv-open 0.2s ease-out;
}
.advanced-content[data-state="closed"] {
    animation: adv-close 0.2s ease-out;
}
@keyframes adv-open {
    from { height: 0; opacity: 0; }
    to { height: var(--reka-collapsible-content-height); opacity: 1; }
}
@keyframes adv-close {
    from { height: var(--reka-collapsible-content-height); opacity: 1; }
    to { height: 0; opacity: 0; }
}

.advanced-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.625rem 0.75rem;
    padding-top: 0.625rem;
}
.advanced-grid > :last-child:nth-child(odd) {
    grid-column: 1 / -1;
}
</style>

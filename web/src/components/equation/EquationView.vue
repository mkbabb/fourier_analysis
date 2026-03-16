<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { watchDebounced, useMediaQuery } from "@vueuse/core";
import { computeEquation, simplifyCoefficients, isAbortError } from "@/lib/equation/api";
import type { NotationMode, ComputeEquationResponse, FourierTermDTO, EquationDisplayMode } from "@/lib/equation/types";
import type { BasisComponent } from "@/lib/types";
import { TIER_INFO, energyColor } from "@/lib/equation/notation";
import { HoverCardRoot, HoverCardTrigger, HoverCardPortal, HoverCardContent } from "reka-ui";
import { Info } from "lucide-vue-next";

import UnderlineTabs from "@/components/ui/UnderlineTabs.vue";
import FunctionInput from "./FunctionInput.vue";
import EquationResult from "./EquationResult.vue";
import EquationModeToggle from "./EquationModeToggle.vue";
import ConvergencePlot from "./ConvergencePlot.vue";
import EqCoefficientsPanel from "./EqCoefficientsPanel.vue";

import { loadCachedInputState, saveCachedInputState, loadCachedResult, saveCachedResult } from "./composables/useEquationCache";
import { useCoeffHover } from "./composables/useCoeffHover";

// ── Input state (restore from cache) ──
const cached = loadCachedInputState();
const expression = ref(cached?.expression ?? "x*(pi - x)");
const domainStart = ref(cached?.domainStart ?? 0);
const domainEnd = ref(cached?.domainEnd ?? Math.PI);
const nHarmonics = ref(cached?.nHarmonics ?? 20);
const budget = ref(cached?.budget ?? 10);
const notation = ref<NotationMode>(cached?.notation ?? "trig");

// ── Result state ──
const computing = ref(false);
const simplifying = ref(false);
const error = ref<string | null>(null);
const cachedRes = loadCachedResult();
const result = ref<ComputeEquationResponse | null>(cachedRes?.result ?? null);
const displayLatex = ref(cachedRes?.latex ?? "");
const displayLatexSigma = ref(cachedRes?.result?.latex_sigma ?? "");
const displayEnergy = ref(cachedRes?.energy ?? 1);
const effectiveN = ref(cachedRes?.result?.effective_n ?? 20);
const autoHarmonics = ref(true);
const eqMode = ref<EquationDisplayMode>("sigma");
const mobileView = ref<"controls" | "canvas">("canvas");
const isDesktop = useMediaQuery("(min-width: 1024px)");
const eqCardRef = ref<HTMLDivElement>();

// ── Derived state ──
const activeLatex = computed(() =>
    eqMode.value === "sigma" && displayLatexSigma.value ? displayLatexSigma.value : displayLatex.value,
);

const vizHarmonics = computed(() =>
    autoHarmonics.value ? Math.min(effectiveN.value, nHarmonics.value) : nHarmonics.value,
);

const loading = computed(() => computing.value || simplifying.value);

const components = computed<BasisComponent[]>(() => {
    if (!result.value) return [];
    return result.value.coefficients.map((c: FourierTermDTO) => ({
        index: c.n,
        coefficient: [c.coefficient_re, c.coefficient_im] as [number, number],
        amplitude: c.amplitude,
        phase: c.phase,
    }));
});

const tierInfo = computed(() => result.value ? (TIER_INFO[result.value.tier] ?? TIER_INFO.spline) : null);
const eColor = computed(() => energyColor(displayEnergy.value));

const coefficients = computed(() => result.value?.coefficients ?? []);

// ── Coefficient hover (composable) ──
const { hoveredCoeff, popoverPos, popoverHtml, onMouseMove: onCoeffMove, onMouseLeave: onCoeffLeave } =
    useCoeffHover(coefficients, notation);

// ── Cache keys ──
let lastComputeKey = cachedRes ? `${expression.value}|${domainStart.value}|${domainEnd.value}|${nHarmonics.value}` : "";
let lastDisplayKey = cachedRes ? `${lastComputeKey}|${notation.value}|${budget.value}` : "";

function computeKey(): string {
    return `${expression.value}|${domainStart.value}|${domainEnd.value}|${nHarmonics.value}`;
}
function displayKey(): string {
    return `${lastComputeKey}|${notation.value}|${budget.value}`;
}

// ── API ──

async function doCompute(force = false) {
    const expr = expression.value.trim();
    if (!expr) return;
    const key = computeKey();
    if (!force && key === lastComputeKey && result.value) {
        await doSimplify();
        return;
    }

    computing.value = true;
    error.value = null;
    try {
        result.value = await computeEquation({
            expression: expr,
            domain_start: domainStart.value,
            domain_end: domainEnd.value,
            n_harmonics: nHarmonics.value,
            n_eval_points: 500,
            notation: notation.value,
            budget: budget.value,
        });
        lastComputeKey = key;
        displayLatex.value = result.value.latex;
        displayLatexSigma.value = result.value.latex_sigma;
        displayEnergy.value = result.value.energy_captured;
        // Capture display key BEFORE effectiveN triggers the vizHarmonics→budget
        // chain, so a subsequent doSimplify can detect the budget changed.
        lastDisplayKey = displayKey();
        effectiveN.value = result.value.effective_n;
        saveCachedResult(result.value, displayLatex.value, displayEnergy.value);
    } catch (e) {
        if (!isAbortError(e)) {
            error.value = e instanceof Error ? e.message : "Computation failed";
        }
    } finally {
        computing.value = false;
    }
}

async function doSimplify() {
    if (!components.value.length) return;
    const key = displayKey();
    if (key === lastDisplayKey) return;

    simplifying.value = true;
    try {
        const resp = await simplifyCoefficients(components.value, budget.value, notation.value);
        displayLatex.value = resp.latex;
        displayEnergy.value = resp.energy_captured;
        lastDisplayKey = key;
        if (result.value) saveCachedResult(result.value, displayLatex.value, displayEnergy.value);
    } catch (e) {
        if (!isAbortError(e)) { /* silent */ }
    } finally {
        simplifying.value = false;
    }
}

// ── Watches ──

watch(vizHarmonics, (v, oldV) => {
    if (budget.value > v) {
        budget.value = Math.max(2, v);
    } else if (oldV != null && oldV > 0 && budget.value <= oldV) {
        // Budget was at or near the old cap — scale it up proportionally
        const ratio = budget.value / oldV;
        budget.value = Math.max(2, Math.round(v * ratio));
    }
});

watch(
    () => [expression.value, domainStart.value, domainEnd.value, nHarmonics.value, budget.value, notation.value],
    () => saveCachedInputState({
        expression: expression.value,
        domainStart: domainStart.value,
        domainEnd: domainEnd.value,
        nHarmonics: nHarmonics.value,
        budget: budget.value,
        notation: notation.value,
    }),
);

// Initial compute (only if no cached result)
if (!result.value) doCompute();

// Cheap re-render on notation/budget change
watchDebounced(
    () => [notation.value, budget.value] as const,
    () => { if (result.value) doSimplify(); },
    { debounce: 200 },
);
</script>

<template>
    <div class="flex flex-col flex-1 min-h-0">
        <!-- Mobile tab bar -->
        <div class="flex px-3 py-1 bg-background lg:hidden">
            <UnderlineTabs
                :options="[{ label: 'Controls', value: 'controls' }, { label: 'Canvas', value: 'canvas' }]"
                :model-value="mobileView"
                @update:model-value="mobileView = $event as 'controls' | 'canvas'" />
        </div>

        <div class="eq-grid">
            <!-- Left panel -->
            <div class="eq-panel-left-wrap" :class="{ 'panel-inactive': mobileView !== 'controls' && !isDesktop }">
                <div class="eq-panel-left">
                    <FunctionInput
                        v-model:expression="expression"
                        v-model:domain-start="domainStart"
                        v-model:domain-end="domainEnd"
                        v-model:n-harmonics="nHarmonics"
                        v-model:budget="budget"
                        v-model:notation="notation"
                        :effective-n="effectiveN"
                        :energy-captured="displayEnergy"
                        :auto-harmonics="autoHarmonics"
                        :viz-harmonics="vizHarmonics"
                        @update:auto-harmonics="autoHarmonics = $event"
                        @compute="doCompute(true)"
                    />
                    <Transition name="slide-down">
                        <EqCoefficientsPanel v-if="components.length" :components="components" />
                    </Transition>
                </div>
            </div>

            <!-- Right panel -->
            <div class="eq-panel-right" :class="{ 'panel-inactive': mobileView !== 'canvas' && !isDesktop }">
                <!-- Loading (no prior result) -->
                <div v-if="computing && !result" class="flex items-center justify-center flex-1">
                    <div class="flex flex-col items-center gap-3">
                        <div class="size-6 animate-spin rounded-full border-2 border-border border-t-primary" />
                        <p class="text-sm text-muted-foreground fira-code">Computing…</p>
                    </div>
                </div>

                <!-- Error (no prior result) -->
                <div v-else-if="error && !result" class="flex items-center justify-center flex-1">
                    <div class="cartoon-card p-4 max-w-md text-center">
                        <p class="text-sm font-medium text-foreground mb-1">Computation failed</p>
                        <p class="text-sm text-muted-foreground fira-code">{{ error }}</p>
                    </div>
                </div>

                <!-- Results -->
                <template v-else-if="result">
                    <!-- Re-compute status banners -->
                    <div v-if="computing" class="cartoon-card px-3 py-2 flex items-center gap-2 text-sm shrink-0">
                        <div class="size-3.5 animate-spin rounded-full border-[1.5px] border-border border-t-primary" />
                        <span class="text-muted-foreground fira-code">Recomputing…</span>
                    </div>
                    <div v-else-if="error" class="cartoon-card px-3 py-2 flex items-center gap-2 text-sm border-red-500/30 bg-red-500/5 shrink-0">
                        <span class="font-medium text-red-400">Error:</span>
                        <span class="text-muted-foreground fira-code truncate">{{ error }}</span>
                    </div>

                    <!-- Equation card -->
                    <div
                        ref="eqCardRef"
                        class="cartoon-card relative eq-card"
                        @mousemove="(e) => onCoeffMove(e, eqCardRef)"
                        @mouseleave="onCoeffLeave"
                    >
                        <EquationResult :latex="activeLatex" />

                        <!-- Per-coefficient popover -->
                        <Transition name="pop">
                            <div
                                v-if="hoveredCoeff && popoverHtml"
                                class="coeff-popover"
                                :style="{ left: `${popoverPos.x}px`, top: `${popoverPos.y}px` }"
                            >
                                <div class="coeff-popover-inner" v-html="popoverHtml" />
                            </div>
                        </Transition>

                        <!-- Mode toggle -->
                        <div class="eq-mode-anchor">
                            <EquationModeToggle v-model="eqMode" />
                        </div>

                        <!-- Info hover card -->
                        <HoverCardRoot v-if="tierInfo" :open-delay="200" :close-delay="150">
                            <HoverCardTrigger as-child>
                                <button class="glass-btn info-anchor">
                                    <svg class="size-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                                    </svg>
                                </button>
                            </HoverCardTrigger>
                            <HoverCardPortal>
                                <HoverCardContent class="info-hovercard" side="bottom" :side-offset="6" :collision-padding="12" align="end">
                                    <div class="flex items-center gap-2 flex-wrap">
                                        <span
                                            class="inline-flex items-center px-2 py-0.5 rounded-full text-sm font-semibold border-[1.5px]"
                                            :style="{
                                                background: `color-mix(in srgb, ${tierInfo.color} 15%, transparent)`,
                                                borderColor: `color-mix(in srgb, ${tierInfo.color} 30%, transparent)`,
                                                color: tierInfo.color,
                                            }"
                                        >{{ tierInfo.label }}</span>
                                        <span class="text-sm font-medium fira-code" :style="{ color: eColor }">
                                            {{ (displayEnergy * 100).toFixed(1) }}% energy
                                        </span>
                                    </div>
                                    <div class="flex gap-1.5 items-start text-sm text-muted-foreground mt-2">
                                        <Info class="size-3.5 shrink-0 mt-0.5" />
                                        <p>{{ tierInfo.description }}</p>
                                    </div>
                                </HoverCardContent>
                            </HoverCardPortal>
                        </HoverCardRoot>
                    </div>

                    <!-- Convergence plot -->
                    <div class="cartoon-card px-3 py-2 flex-1 min-h-0 flex flex-col">
                        <ConvergencePlot
                            class="flex-1"
                            :original-points="result.original_points"
                            :coefficients="result.coefficients"
                            :n-harmonics="vizHarmonics"
                            :domain="[domainStart, domainEnd]"
                            :expression="expression"
                        />
                    </div>
                </template>

                <!-- Empty state -->
                <div v-else class="flex items-center justify-center flex-1">
                    <p class="text-sm text-muted-foreground cm-serif italic">
                        Enter a function to see its Fourier series
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
@reference "tailwindcss";

/* ── Grid layout ── */
.eq-grid {
    @apply flex flex-col flex-1 min-h-0 p-1 gap-1;
}
@media (min-width: 1024px) {
    .eq-grid {
        display: grid;
        grid-template-columns: 360px 1fr;
        grid-template-rows: 1fr;
        gap: 0.5rem;
        padding: 0.5rem;
        padding-bottom: 0.75rem;
        overflow: hidden;
    }
}
@media (min-width: 1280px) { .eq-grid { grid-template-columns: 400px 1fr; } }
@media (min-width: 1536px) { .eq-grid { grid-template-columns: 440px 1fr; } }

/* ── Left panel ── */
.eq-panel-left-wrap {
    @apply relative flex flex-col w-full min-h-0;
    max-width: 480px;
    margin: 0 auto;
    overflow-x: visible;
    overflow-y: clip;
    flex: 1;
}
@media (max-width: 1023px) { .eq-panel-left-wrap { overflow: visible; flex: none; } }
@media (min-width: 1024px) { .eq-panel-left-wrap { max-width: none; margin: 0; } }

.eq-panel-left-wrap::after {
    content: '';
    @apply absolute bottom-0 left-0 right-0 pointer-events-none;
    height: 2.5rem;
    background: linear-gradient(to bottom, transparent, hsl(var(--background)));
    z-index: 2;
}
@media (max-width: 1023px) { .eq-panel-left-wrap::after { display: none; } }

.eq-panel-left {
    @apply flex flex-col gap-3 w-full pb-8 overflow-y-auto min-h-0 flex-1;
}
@media (min-width: 1024px) { .eq-panel-left { padding-right: 0.25rem; } }

/* ── Right panel ── */
.eq-panel-right {
    @apply flex flex-col gap-3 min-h-0 min-w-0 flex-1;
    overflow-y: auto;
    overflow-x: hidden;
}

/* ── Equation card ── */
.eq-card {
    height: 10rem;
    flex-shrink: 0;
    overflow: hidden;
}

/* ── Coefficient popover ── */
.coeff-popover {
    @apply absolute pointer-events-none rounded-lg;
    transform: translateX(-50%);
    z-index: 25;
    min-width: 160px;
    max-width: 320px;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--background) / 0.95);
    backdrop-filter: blur(16px);
    border: 1px solid hsl(var(--border));
    box-shadow: 0 4px 12px hsl(var(--foreground) / 0.08);
}

.coeff-popover-inner :deep(.katex-display) {
    margin: 0;
    padding: 0;
    overflow: visible !important;
}
.coeff-popover-inner :deep(.katex) {
    font-size: 1em;
    text-align: left;
}

/* ── Golden hover on sigma coefficients ── */
.eq-card :deep(.eq-coeff) {
    cursor: pointer;
    border-radius: 3px;
    padding: 0 2px;
    transition: color 0.12s ease, background 0.12s ease;
}
.eq-card :deep(.eq-coeff:hover) {
    color: #f0b632 !important;
    background: rgba(240, 182, 50, 0.1);
}

/* ── Anchors ── */
.eq-mode-anchor {
    @apply absolute top-2 left-2;
    z-index: 20;
}
.info-anchor {
    @apply absolute top-2;
    right: 3.25rem;
    z-index: 30;
}

/* ── Mobile panel toggle ── */
@media (max-width: 1023px) {
    .panel-inactive {
        display: none;
    }
}

/* ── Transitions ── */
.pop-enter-active  { transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1); }
.pop-leave-active  { transition: all 0.1s ease; }
.pop-enter-from    { opacity: 0; transform: translateY(-4px) scale(0.97); }
.pop-leave-to      { opacity: 0; transform: translateY(-2px) scale(0.98); }

.slide-down-enter-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from   { opacity: 0; transform: translateY(-8px); }
.slide-down-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>

<!-- Global style for portaled HoverCard content -->
<style>
.info-hovercard {
    z-index: 100;
    width: 300px;
    padding: 0.75rem;
    color: hsl(var(--popover-foreground));
    background: hsl(var(--popover));
    border: 1.5px solid hsl(var(--border));
    border-radius: 0.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    animation: tooltip-in 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    user-select: none;
}
</style>

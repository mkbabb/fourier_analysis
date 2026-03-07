<script setup lang="ts">
import { ref, computed } from "vue";
import { useAnimationStore } from "@/stores/animation";
import { useSessionStore } from "@/stores/session";
import { Play, Pause, Download, Copy, Check } from "lucide-vue-next";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const props = withDefaults(
    defineProps<{
        activeBases?: string[];
    }>(),
    { activeBases: () => ["fourier-epicycles"] },
);

const emit = defineEmits<{
    (e: "exportFrame"): void;
}>();

const anim = useAnimationStore();
const store = useSessionStore();

const copied = ref(false);
async function copySlug() {
    if (!store.slug) return;
    const url = `${window.location.origin}/s/${store.slug}`;
    await navigator.clipboard.writeText(url);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
}

const nComponents = computed(() => store.epicycleData?.components?.length ?? 0);
const seriesN = computed(() => {
    if (store.basesData) {
        const levels = store.basesData.levels;
        const idx = Math.max(0, Math.min(levels.length - 1, Math.floor(anim.t * levels.length)));
        return levels[idx];
    }
    return Math.max(1, Math.ceil(anim.t * nComponents.value));
});

const speedStr = computed({
    get: () => String(anim.speed),
    set: (v: string) => { anim.speed = parseFloat(v); },
});

function onScrub(e: Event) {
    const input = e.target as HTMLInputElement;
    anim.seek(parseFloat(input.value));
}
</script>

<template>
    <div class="px-3 py-2 backdrop-blur-sm bg-background/60 border-t border-foreground/10">
        <div class="flex items-center gap-2.5">
            <!-- Play/Pause -->
            <button
                class="play-btn flex-shrink-0"
                :class="{ 'is-playing': anim.playing }"
                @click="anim.toggle"
                :title="anim.playing ? 'Pause' : 'Play'"
            >
                <Transition name="icon-swap" mode="out-in">
                    <Pause v-if="anim.playing" class="h-3.5 w-3.5" />
                    <Play v-else class="h-3.5 w-3.5" />
                </Transition>
                <span class="play-label">{{ anim.playing ? 'Pause' : 'Play' }}</span>
            </button>

            <!-- Timeline scrubber — green -->
            <div class="flex-1 px-1">
                <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.001"
                    :value="anim.t"
                    class="timeline-slider w-full"
                    @input="onScrub"
                />
            </div>

            <!-- Time display -->
            <span class="w-20 text-right fira-code text-xs text-muted-foreground tabular-nums flex-shrink-0">
                <template v-if="props.activeBases.length === 1 && props.activeBases[0] === 'fourier-epicycles' && !store.basesData">
                    {{ (anim.t * 100).toFixed(1) }}%
                </template>
                <template v-else>
                    N={{ seriesN }}
                </template>
            </span>

            <!-- Speed dropdown (reka-ui Select) -->
            <Select v-model="speedStr">
                <SelectTrigger class="h-8 w-[4.5rem] flex-shrink-0 fira-code text-xs border-2 border-foreground/15 rounded-lg">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="0.25">0.25×</SelectItem>
                    <SelectItem value="0.5">0.5×</SelectItem>
                    <SelectItem value="1">1×</SelectItem>
                    <SelectItem value="2">2×</SelectItem>
                    <SelectItem value="4">4×</SelectItem>
                </SelectContent>
            </Select>

            <!-- Copy session URL -->
            <button
                v-if="store.slug && store.hasImage"
                class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border-2 border-foreground/15 bg-background text-foreground hover:bg-muted transition-all duration-150 hover:scale-105 active:scale-95 cursor-pointer"
                title="Copy session URL"
                @click="copySlug"
            >
                <Transition name="icon-swap" mode="out-in">
                    <Check v-if="copied" class="h-3.5 w-3.5 text-green-500" />
                    <Copy v-else class="h-3.5 w-3.5" />
                </Transition>
            </button>

            <!-- Export frame -->
            <button
                class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border-2 border-foreground/15 bg-background text-foreground hover:bg-muted transition-all duration-150 hover:scale-105 active:scale-95 cursor-pointer"
                title="Export frame as PNG"
                @click="emit('exportFrame')"
            >
                <Download class="h-3.5 w-3.5" />
            </button>
        </div>
    </div>
</template>

<style scoped>
/* Rainbow gradient play button */
.play-btn {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    min-width: 5.25rem;
    justify-content: center;
    padding: 0.375rem 0.875rem;
    border-radius: 9999px;
    cursor: pointer;
    overflow: hidden;
    border: none;
    background: transparent;
    color: #000;
    transition: transform 0.2s, box-shadow 0.2s;
    flex-shrink: 0;
}
.play-label {
    font-size: 0.8125rem;
    font-weight: 600;
    display: inline;
}
@media (max-width: 639px) {
    .play-btn { min-width: 2.25rem; padding: 0.375rem; }
    .play-label { display: none; }
}
:where(.dark) .play-btn {
    color: #fff;
}
.play-btn:hover {
    transform: scale(1.08);
    box-shadow: 0 0 12px rgba(255, 100, 100, 0.15), 0 0 12px rgba(100, 100, 255, 0.15);
}
.play-btn:active {
    transform: scale(0.92);
}
/* Pastel rainbow background (default / paused) */
.play-btn::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 9999px;
    background: linear-gradient(135deg, hsl(0 60% 82%), hsl(40 55% 80%), hsl(120 40% 78%), hsl(200 50% 80%), hsl(280 45% 82%), hsl(340 55% 80%));
    z-index: -1;
    transition: filter 0.3s ease;
}
/* Animated vivid rainbow when playing */
.play-btn.is-playing::before {
    background: linear-gradient(90deg, hsl(0 80% 68%), hsl(40 80% 65%), hsl(120 60% 60%), hsl(200 70% 62%), hsl(280 60% 65%), hsl(340 75% 68%), hsl(0 80% 68%));
    background-size: 200% 100%;
    animation: rainbow-shift 3s linear infinite;
}
:where(.dark) .play-btn::before {
    background: linear-gradient(135deg, hsl(0 30% 40%), hsl(40 28% 38%), hsl(120 22% 36%), hsl(200 28% 38%), hsl(280 24% 40%), hsl(340 28% 38%));
}
:where(.dark) .play-btn.is-playing::before {
    background: linear-gradient(90deg, hsl(0 65% 50%), hsl(40 65% 48%), hsl(120 50% 45%), hsl(200 55% 48%), hsl(280 50% 50%), hsl(340 60% 50%), hsl(0 65% 50%));
    background-size: 200% 100%;
    animation: rainbow-shift 3s linear infinite;
}
@keyframes rainbow-shift {
    0% { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}

/* Timeline slider */
.timeline-slider {
    -webkit-appearance: none;
    appearance: none;
    height: 8px;
    border-radius: 4px;
    background: linear-gradient(
        to right,
        hsl(8 95% 55%) v-bind('(anim.t * 100) + "%"'),
        hsl(var(--foreground) / 0.12) v-bind('(anim.t * 100) + "%"')
    );
    outline: none;
    cursor: pointer;
    transition: background 0.05s ease;
}

:where(.dark) .timeline-slider {
    background: linear-gradient(
        to right,
        hsl(8 70% 42%) v-bind('(anim.t * 100) + "%"'),
        hsl(var(--foreground) / 0.1) v-bind('(anim.t * 100) + "%"')
    );
}

.timeline-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: hsl(8 85% 50%);
    cursor: pointer;
    border: 2px solid hsl(var(--background));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275),
                box-shadow 0.15s ease;
}

:where(.dark) .timeline-slider::-webkit-slider-thumb {
    background: hsl(8 65% 45%);
}

.timeline-slider::-webkit-slider-thumb:hover {
    transform: scale(1.2);
    box-shadow: 0 2px 8px rgba(255, 52, 18, 0.3);
}

.timeline-slider::-webkit-slider-thumb:active {
    transform: scale(0.95);
}

.timeline-slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: hsl(8 85% 50%);
    cursor: pointer;
    border: 2px solid hsl(var(--background));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.timeline-slider::-moz-range-progress {
    background: hsl(8 95% 55%);
    border-radius: 4px;
    height: 8px;
}

.timeline-slider::-moz-range-track {
    background: hsl(var(--secondary));
    border-radius: 4px;
    height: 8px;
}

.icon-swap-enter-active,
.icon-swap-leave-active {
    transition: all 0.15s ease;
}
.icon-swap-enter-from {
    opacity: 0;
    transform: scale(0.7);
}
.icon-swap-leave-to {
    opacity: 0;
    transform: scale(0.7);
}
</style>

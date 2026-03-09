<script setup lang="ts">
import { ref, computed } from "vue";
import { onClickOutside } from "@vueuse/core";
import { useAnimationStore } from "@/stores/animation";
import { useSessionStore } from "@/stores/session";
import { VIZ_COLORS } from "@/lib/colors";
import {
    Download,
    Eye,
    EyeOff,
    EllipsisVertical,
} from "lucide-vue-next";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Tooltip } from "@/components/ui/tooltip";

const props = withDefaults(
    defineProps<{
        activeBases?: string[];
        showGhost?: boolean;
    }>(),
    { activeBases: () => ["fourier-epicycles"], showGhost: true },
);

const emit = defineEmits<{
    (e: "exportFrame"): void;
    (e: "toggleGhost"): void;
}>();

const anim = useAnimationStore();
const store = useSessionStore();

const isEpicycleOnly = computed(() =>
    props.activeBases.includes("fourier-epicycles") && props.activeBases.length === 1,
);

const currentLevel = computed(() => {
    const basesData = store.basesData;
    const epicycleData = store.epicycleData;
    if (basesData && basesData.levels.length > 0) {
        const levels = basesData.levels;
        const pos = anim.t * (levels.length - 1);
        return levels[Math.round(pos)];
    } else if (epicycleData) {
        return Math.max(1, Math.ceil(anim.t * epicycleData.components.length));
    }
    return 1;
});

const caretLabel = computed(() => {
    if (isEpicycleOnly.value) {
        return `t = ${anim.t.toFixed(2)}`;
    }
    return `N = ${currentLevel.value}`;
});

const speedStr = computed({
    get: () => String(anim.speed),
    set: (v: string) => {
        anim.speed = parseFloat(v);
    },
});

function onScrub(e: Event) {
    const input = e.target as HTMLInputElement;
    anim.seek(parseFloat(input.value));
}

/* Slider color: green for epicycles, red otherwise */
const isEpicycleMode = computed(() =>
    props.activeBases.includes("fourier-epicycles"),
);
const sliderColor = computed(() =>
    isEpicycleMode.value ? VIZ_COLORS.green : VIZ_COLORS.fourier,
);
const sliderColorDark = computed(() =>
    isEpicycleMode.value ? VIZ_COLORS.greenDark : VIZ_COLORS.redDark,
);

/* Three-dot menu */
const menuOpen = ref(false);
const menuAnchor = ref<HTMLElement>();

onClickOutside(menuAnchor, () => { menuOpen.value = false });
</script>

<template>
    <div class="anim-controls">
        <!-- Play/Pause — icon-only pill -->
        <Tooltip :text="anim.playing ? 'Pause animation' : 'Play animation'">
            <button
                class="play-btn"
                :class="{ 'is-playing': anim.playing }"
                @click="anim.toggle"
            >
                <Transition name="icon-swap" mode="out-in">
                    <svg v-if="anim.playing" class="play-icon" viewBox="0 0 320 512" fill="currentColor"><path d="M48 64C21.5 64 0 85.5 0 112L0 400c0 26.5 21.5 48 48 48l32 0c26.5 0 48-21.5 48-48l0-288c0-26.5-21.5-48-48-48L48 64zm192 0c-26.5 0-48 21.5-48 48l0 288c0 26.5 21.5 48 48 48l32 0c26.5 0 48-21.5 48-48l0-288c0-26.5-21.5-48-48-48l-32 0z"/></svg>
                    <svg v-else class="play-icon" viewBox="0 0 384 512" fill="currentColor"><path d="M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80L0 432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z"/></svg>
                </Transition>
            </button>
        </Tooltip>

        <!-- Timeline slider — fills remaining space -->
        <div class="timeline-row">
            <div class="timeline-caret" :style="{ left: (anim.t * 100) + '%' }">
                <span class="caret-value fira-code">{{ caretLabel }}</span>
            </div>
            <input
                type="range"
                min="0"
                max="1"
                step="0.001"
                :value="anim.t"
                class="timeline-slider styled-slider w-full"
                :style="{
                    '--slider-color': sliderColor,
                    '--slider-color-dark': sliderColorDark,
                }"
                @input="onScrub"
                @pointerdown="anim.startScrub"
                @pointerup="anim.endScrub"
                @pointercancel="anim.endScrub"
            />
        </div>

        <!-- Speed dropdown — visible on desktop only -->
        <Tooltip text="Playback speed">
            <div class="speed-desktop">
                <Select v-model="speedStr">
                    <SelectTrigger class="speed-trigger">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="0.25">0.25&times;</SelectItem>
                        <SelectItem value="0.5">0.5&times;</SelectItem>
                        <SelectItem value="1">1&times;</SelectItem>
                        <SelectItem value="2">2&times;</SelectItem>
                        <SelectItem value="4">4&times;</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </Tooltip>

        <!-- Three-dot menu -->
        <div ref="menuAnchor" class="menu-anchor">
            <Tooltip text="More options">
                <button
                    class="menu-btn"
                    @click="menuOpen = !menuOpen"
                >
                    <EllipsisVertical class="h-4 w-4" />
                </button>
            </Tooltip>
            <Transition name="popup">
                <div v-if="menuOpen" class="menu-popup">
                    <!-- Speed — mobile only (inside menu) -->
                    <div class="speed-mobile">
                        <span class="menu-label text-muted-foreground">Speed</span>
                        <Select v-model="speedStr">
                            <SelectTrigger class="speed-trigger-compact">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="0.25">0.25&times;</SelectItem>
                                <SelectItem value="0.5">0.5&times;</SelectItem>
                                <SelectItem value="1">1&times;</SelectItem>
                                <SelectItem value="2">2&times;</SelectItem>
                                <SelectItem value="4">4&times;</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <Tooltip :text="props.showGhost ? 'Hide original contour' : 'Show original contour'">
                        <button
                            @click="emit('toggleGhost')"
                            class="menu-item"
                        >
                            <component :is="props.showGhost ? Eye : EyeOff" class="h-4 w-4" />
                            <span class="menu-label">Outline</span>
                        </button>
                    </Tooltip>
                    <Tooltip text="Export frame as PNG">
                        <button
                            @click="emit('exportFrame')"
                            class="menu-item"
                        >
                            <Download class="h-4 w-4" />
                            <span class="menu-label">Export</span>
                        </button>
                    </Tooltip>
                </div>
            </Transition>
        </div>
    </div>
</template>

<style scoped>
/* Single-row flex layout */
.anim-controls {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.375rem;
    background: transparent;
    border-top: none;
    min-width: 0;
    z-index: 20;
}

/* Play/Pause — wide rounded-rect pill (keyframes.js style) */
.play-btn {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.25rem;
    height: 1.75rem;
    border-radius: 0.5rem;
    cursor: pointer;
    overflow: hidden;
    border: none;
    background: transparent;
    color: #fff;
    flex-shrink: 0;
    transition: transform 0.2s, box-shadow 0.2s;
}

/* Vivid rainbow background */
.play-btn::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 0.5rem;
    background: linear-gradient(
        90deg,
        hsl(0 78% 68%),
        hsl(30 85% 65%),
        hsl(55 80% 62%),
        hsl(120 55% 58%),
        hsl(200 70% 62%),
        hsl(270 60% 65%),
        hsl(330 72% 66%),
        hsl(0 78% 68%)
    );
    background-size: 200% 100%;
    z-index: -1;
    transition: filter 0.3s ease;
}
/* Animated shift when playing */
.play-btn.is-playing::before {
    animation: rainbow-shift 3s linear infinite;
}

.play-btn:hover {
    transform: scale(1.08);
    box-shadow: 0 2px 16px rgba(255, 100, 100, 0.25),
        0 2px 16px rgba(100, 100, 255, 0.2);
}
.play-btn:active {
    transform: scale(0.93);
}

.play-icon {
    width: 13px;
    height: 13px;
}

@keyframes rainbow-shift {
    0% {
        background-position: 0% 50%;
    }
    100% {
        background-position: 200% 50%;
    }
}

/* Timeline slider — fills remaining space */
.timeline-row {
    flex: 1;
    min-width: 0;
    padding: 0 0.25rem;
    position: relative;
}

.timeline-caret {
    position: absolute;
    bottom: calc(100% + 2px);
    transform: translateX(-50%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 30;
}

/* Show caret on hover or when scrubbing */
.timeline-row:hover .timeline-caret,
.timeline-row:has(input:active) .timeline-caret {
    opacity: 1;
}

.caret-value {
    display: block;
    padding: 0.125rem 0.375rem;
    font-size: 0.6875rem;
    font-weight: 500;
    color: hsl(var(--popover-foreground));
    background: hsl(var(--popover));
    border: 1px solid hsl(var(--border));
    border-radius: 0.25rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    white-space: nowrap;
}

/* Timeline slider overrides — custom track background with v-bind progress */
.timeline-slider {
    --progress: v-bind('(anim.t * 100) + "%"');
    height: 12px;
    border-radius: 6px;
    background: linear-gradient(
        to right,
        var(--slider-color) var(--progress),
        hsl(var(--foreground) / 0.12) var(--progress)
    );
}

.timeline-slider::-webkit-slider-thumb {
    background: var(--slider-color);
}

.timeline-slider::-moz-range-thumb {
    background: var(--slider-color);
}

.timeline-slider::-moz-range-progress {
    border-radius: 6px;
    height: 12px;
}

.timeline-slider::-moz-range-track {
    border-radius: 6px;
    height: 12px;
}

:where(.dark) .timeline-slider {
    background: linear-gradient(
        to right,
        var(--slider-color-dark) var(--progress),
        hsl(var(--foreground) / 0.1) var(--progress)
    );
}

:where(.dark) .timeline-slider::-webkit-slider-thumb {
    background: var(--slider-color-dark);
}

:where(.dark) .timeline-slider::-moz-range-progress {
    background: var(--slider-color-dark);
}

/* Speed dropdown — desktop only */
.speed-desktop {
    display: none;
}
@media (min-width: 640px) {
    .speed-desktop {
        display: block;
    }
}

/* Speed dropdown — mobile only (inside menu) */
.speed-mobile {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    border-bottom: 1px solid hsl(var(--border) / 0.5);
    margin-bottom: 0.125rem;
    padding-bottom: 0.5rem;
}
@media (min-width: 640px) {
    .speed-mobile {
        display: none;
    }
}

.speed-trigger {
    height: 1.75rem;
    width: 3.5rem;
    flex-shrink: 0;
    font-family: "Fira Code", monospace;
    font-size: 0.75rem;
    border: none;
    background: none;
    border-radius: 0.375rem;
    color: hsl(var(--muted-foreground));
}

.speed-trigger-compact {
    height: 2rem;
    width: 4rem;
    flex-shrink: 0;
    font-family: "Fira Code", monospace;
    font-size: 0.75rem;
    border: 1.5px solid hsl(var(--foreground) / 0.15);
    border-radius: 0.375rem;
}

/* Three-dot menu */
.menu-anchor {
    position: relative;
}

.menu-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 0.375rem;
    border: none;
    background: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all 0.15s;
    flex-shrink: 0;
    padding: 0;
}
.menu-btn:hover {
    color: hsl(var(--foreground));
    transform: scale(1.1);
}
.menu-btn:active {
    transform: scale(0.95);
}

.menu-popup {
    position: absolute;
    bottom: calc(100% + 0.5rem);
    right: 0;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    padding: 0.375rem;
    background: hsl(var(--card));
    border: 2px solid hsl(var(--foreground) / 0.15);
    border-radius: 0.75rem;
    box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.1);
    z-index: 30;
}

.menu-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: none;
    background: none;
    color: hsl(var(--foreground));
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
    font-size: 0.8125rem;
    font-weight: 500;
}
.menu-item:hover {
    background: hsl(var(--muted));
}

/* Popup transition */
.popup-enter-active,
.popup-leave-active {
    transition: opacity 0.15s ease, transform 0.15s ease;
}
.popup-enter-from,
.popup-leave-to {
    opacity: 0;
    transform: translateY(4px) scale(0.95);
}

/* Icon swap transition */
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

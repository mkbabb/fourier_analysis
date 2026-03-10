<script setup lang="ts">
import { ref, computed } from "vue";
import { onClickOutside } from "@vueuse/core";
import { useAnimationStore } from "@/stores/animation";
import { useSessionStore } from "@/stores/session";
import {
    Download,
    Eye,
    EyeOff,
    EllipsisVertical,
} from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";
import EasingPicker from "./EasingPicker.vue";
import SpeedSelect from "./SpeedSelect.vue";

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
        const pos = anim.easedT * (levels.length - 1);
        return levels[Math.round(pos)];
    } else if (epicycleData) {
        return Math.max(1, Math.ceil(anim.easedT * epicycleData.components.length));
    }
    return 1;
});

const caretLabel = computed(() => {
    if (isEpicycleOnly.value) {
        return `t = ${anim.t.toFixed(2)}`;
    }
    return `N = ${currentLevel.value}`;
});

/* ── Glass timeline slider ────────────────────────────── */
const trackRef = ref<HTMLElement>();
const scrubbing = ref(false);

function tFromPointer(e: PointerEvent): number {
    const rect = trackRef.value!.getBoundingClientRect();
    return Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
}

function onTrackDown(e: PointerEvent) {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    scrubbing.value = true;
    anim.startScrub();
    anim.seek(tFromPointer(e));
}

function onTrackMove(e: PointerEvent) {
    if (!scrubbing.value) return;
    anim.seek(tFromPointer(e));
}

function onTrackUp() {
    scrubbing.value = false;
    anim.endScrub();
}

function onTrackKeydown(e: KeyboardEvent) {
    const step = e.shiftKey ? 0.1 : 0.01;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
        e.preventDefault();
        anim.seek(Math.min(1, anim.t + step));
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
        e.preventDefault();
        anim.seek(Math.max(0, anim.t - step));
    }
}

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

        <!-- Timeline slider — glassmorphic custom track -->
        <div class="timeline-row">
            <div class="timeline-caret" :style="{ left: (anim.t * 100) + '%' }">
                <span class="caret-value fira-code">{{ caretLabel }}</span>
            </div>
            <div
                ref="trackRef"
                class="glass-track"
                role="slider"
                tabindex="0"
                :aria-valuenow="anim.t"
                aria-valuemin="0"
                aria-valuemax="1"
                aria-label="Timeline"
                @pointerdown="onTrackDown"
                @pointermove="onTrackMove"
                @pointerup="onTrackUp"
                @pointercancel="onTrackUp"
                @keydown="onTrackKeydown"
            >
                <div class="glass-fill" :style="{ width: (anim.t * 100) + '%' }" />
                <div class="glass-thumb" :style="{ left: (anim.t * 100) + '%' }" />
            </div>
        </div>

        <!-- Speed dropdown — visible on desktop only -->
        <Tooltip text="Playback speed">
            <div class="desktop-only">
                <SpeedSelect :model-value="anim.speed" @update:model-value="anim.speed = $event" />
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
                    <!-- Speed — mobile only -->
                    <div class="mobile-only menu-row">
                        <span class="menu-label text-muted-foreground">Speed</span>
                        <SpeedSelect :model-value="anim.speed" @update:model-value="anim.speed = $event" compact />
                    </div>

                    <EasingPicker />

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

/* Play/Pause — glassy rainbow pill */
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
    border: 1px solid rgba(255, 255, 255, 0.25);
    background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.15) 0%,
        rgba(255, 255, 255, 0.05) 100%
    );
    backdrop-filter: blur(12px) saturate(1.4);
    -webkit-backdrop-filter: blur(12px) saturate(1.4);
    color: #fff;
    flex-shrink: 0;
    transition: transform 0.2s, box-shadow 0.3s, border-color 0.3s;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.2),
        inset 0 -1px 0 rgba(0, 0, 0, 0.05),
        0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Rainbow gradient layer */
.play-btn::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 0.5rem;
    background: linear-gradient(
        135deg,
        hsl(0 75% 62% / 0.55),
        hsl(35 85% 58% / 0.5),
        hsl(55 80% 55% / 0.45),
        hsl(140 50% 50% / 0.45),
        hsl(210 65% 58% / 0.5),
        hsl(275 55% 58% / 0.5),
        hsl(330 65% 58% / 0.55)
    );
    background-size: 300% 300%;
    z-index: -1;
    transition: opacity 0.3s ease;
}

/* Glass highlight edge */
.play-btn::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 0.5rem;
    background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.25) 0%,
        rgba(255, 255, 255, 0) 50%
    );
    pointer-events: none;
}

/* Only animate rainbow when playing */
.play-btn.is-playing::before {
    animation: rainbow-drift 2.5s ease infinite;
}

.play-btn:hover {
    transform: scale(1.08);
    border-color: rgba(255, 255, 255, 0.4);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.25),
        0 4px 20px rgba(200, 100, 255, 0.2),
        0 2px 12px rgba(100, 180, 255, 0.15);
}
.play-btn:active {
    transform: scale(0.93);
}

.play-icon {
    width: 13px;
    height: 13px;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.15));
}

@keyframes rainbow-drift {
    0% { background-position: 0% 0%; }
    50% { background-position: 100% 100%; }
    100% { background-position: 0% 0%; }
}

/* Timeline slider — fills remaining space */
.timeline-row {
    flex: 1;
    min-width: 0;
    padding: 0 0.25rem;
    position: relative;
    display: flex;
    align-items: center;
}

.timeline-caret {
    position: absolute;
    bottom: calc(100% + 2px);
    transform: translateX(-50%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 30;
    user-select: none;
    -webkit-user-select: none;
}

/* Show caret on hover or when scrubbing */
.timeline-row:hover .timeline-caret,
.timeline-row:has(.glass-track:active) .timeline-caret {
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

/* Glassmorphic timeline track */
.glass-track {
    position: relative;
    width: 100%;
    height: 18px;
    border-radius: 9px;
    background: hsl(var(--foreground) / 0.05);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    cursor: pointer;
    touch-action: none;
    overflow: hidden;
    transition: background 0.2s;
    outline: none;
}
.glass-track:hover,
.glass-track:focus-visible {
    background: hsl(var(--foreground) / 0.08);
}
.glass-track:focus-visible {
    box-shadow: 0 0 0 2px hsl(var(--ring) / 0.4);
}

.glass-fill {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    background: hsl(var(--foreground) / 0.07);
    border-radius: 9px;
    pointer-events: none;
}

.glass-thumb {
    position: absolute;
    top: 50%;
    transform: translate(calc(-50% - 3px), -50%);
    width: 4px;
    height: 12px;
    border-radius: 2px;
    background: hsl(var(--foreground) / 0.25);
    opacity: 0;
    pointer-events: none;
    transition: all 0.15s ease;
}
.glass-track:hover .glass-thumb {
    opacity: 1;
    width: 6px;
    height: 14px;
    background: hsl(var(--foreground) / 0.4);
}

/* Desktop-only controls */
.desktop-only {
    display: none;
}
@media (min-width: 640px) {
    .desktop-only {
        display: block;
    }
}

/* Mobile-only controls (inside menu) */
.mobile-only {
    display: flex;
}
@media (min-width: 640px) {
    .mobile-only {
        display: none;
    }
}

.menu-row {
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    border-bottom: 1px solid hsl(var(--border) / 0.5);
    margin-bottom: 0.125rem;
    padding-bottom: 0.5rem;
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

<script setup lang="ts">
import { useAnimationStore } from "@/stores/animation";
import { Play, Pause, RotateCcw } from "lucide-vue-next";

const anim = useAnimationStore();

function onScrub(e: Event) {
    const input = e.target as HTMLInputElement;
    anim.seek(parseFloat(input.value));
}
</script>

<template>
    <div class="rounded-xl border border-border bg-card p-4 transition-all duration-200 animate-fade-in">
        <div class="flex items-center gap-3">
            <!-- Play/Pause -->
            <button
                class="flex h-9 w-9 items-center justify-center rounded-lg border border-border transition-all duration-200 hover:bg-muted hover:border-muted-foreground/30 btn-press"
                :class="{ 'bg-primary text-primary-foreground border-primary hover:bg-primary/90 hover:border-primary/90': anim.playing }"
                @click="anim.toggle"
                :title="anim.playing ? 'Pause' : 'Play'"
            >
                <Transition name="icon-swap" mode="out-in">
                    <Pause v-if="anim.playing" class="h-4 w-4" />
                    <Play v-else class="h-4 w-4" />
                </Transition>
            </button>

            <!-- Reset -->
            <button
                class="flex h-9 w-9 items-center justify-center rounded-lg border border-border transition-all duration-200 hover:bg-muted hover:border-muted-foreground/30 btn-press"
                @click="anim.reset"
                title="Reset"
            >
                <RotateCcw class="h-4 w-4" />
            </button>

            <!-- Timeline scrubber -->
            <div class="flex-1">
                <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.001"
                    :value="anim.t"
                    class="w-full"
                    @input="onScrub"
                />
            </div>

            <!-- Time display -->
            <span class="w-14 text-right fira-code text-xs text-muted-foreground tabular-nums">
                {{ (anim.t * 100).toFixed(1) }}%
            </span>

            <!-- Speed -->
            <select
                v-model.number="anim.speed"
                class="rounded-lg border border-input bg-background px-2 py-1.5 fira-code text-xs transition-colors duration-200 focus:border-primary focus:outline-none"
            >
                <option :value="0.25">0.25x</option>
                <option :value="0.5">0.5x</option>
                <option :value="1">1x</option>
                <option :value="2">2x</option>
                <option :value="4">4x</option>
            </select>
        </div>
    </div>
</template>

<style scoped>
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

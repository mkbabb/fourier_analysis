<script setup lang="ts">
import { ref } from "vue";
import { useSessionStore } from "@/stores/session";
import { Share2, Check } from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";
import PathPreview from "@/components/ui/PathPreview.vue";
import { VIZ_COLORS } from "@/lib/colors";

const store = useSessionStore();
const copied = ref(false);

async function copyShareUrl() {
    if (!store.slug || !store.hasImage) return;
    const url = `${window.location.origin}/s/${store.slug}`;
    await navigator.clipboard.writeText(url);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
}
</script>

<template>
    <Tooltip side="bottom">
        <template #content>
            <div class="share-tooltip" @click="copyShareUrl">
                <div v-if="store.epicycleData" class="share-tooltip-grid">
                    <PathPreview
                        :path-x="store.epicycleData.path.x"
                        :path-y="store.epicycleData.path.y"
                        :size="80"
                        :stroke-width="1.5"
                        :stroke-color="VIZ_COLORS.fourier"
                        class="share-tooltip-preview"
                    />
                    <Transition name="copied-fade">
                        <div v-if="copied" class="share-tooltip-copied">
                            <Check class="h-5 w-5" />
                        </div>
                    </Transition>
                </div>
                <hr v-if="store.epicycleData" class="share-tooltip-divider" />
                <span class="share-tooltip-desc">
                    {{ copied ? 'Link copied!' : 'Share your image animation' }}
                </span>
            </div>
        </template>
        <button class="share-btn" @click="copyShareUrl">
            <Transition name="icon-swap" mode="out-in">
                <Check v-if="copied" class="h-5 w-5 text-green-500" />
                <Share2 v-else class="h-5 w-5" />
            </Transition>
        </button>
    </Tooltip>
</template>

<style scoped>
.share-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.75rem;
    height: 2.75rem;
    border: none;
    background: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: all 0.15s ease;
    padding: 0;
}

.share-btn:hover {
    color: hsl(var(--foreground));
    transform: scale(1.1);
}

.share-btn:active {
    transform: scale(0.95);
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

<style>
/* Share tooltip (global — renders in portal) */
.share-tooltip {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
    cursor: pointer;
}
.share-tooltip-grid {
    position: relative;
    border-radius: 0.375rem;
    overflow: hidden;
    background-color: hsl(var(--card));
    background-image:
        linear-gradient(hsl(var(--foreground) / 0.06) 1px, transparent 1px),
        linear-gradient(90deg, hsl(var(--foreground) / 0.06) 1px, transparent 1px);
    background-size: 10px 10px;
}
.share-tooltip-preview {
    position: relative;
    z-index: 1;
}
.share-tooltip-copied {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    background: hsl(var(--card) / 0.8);
    color: #22c55e;
    border-radius: 0.375rem;
}
.copied-fade-enter-active {
    transition: opacity 0.2s ease;
}
.copied-fade-leave-active {
    transition: opacity 0.3s ease;
}
.copied-fade-enter-from,
.copied-fade-leave-to {
    opacity: 0;
}
.share-tooltip-divider {
    width: 100%;
    border: none;
    border-top: 1px solid hsl(var(--border) / 0.5);
    margin: 0;
}
.share-tooltip-desc {
    font-size: 0.8125rem;
    font-weight: 500;
    white-space: nowrap;
    animation: gold-pulse 2.5s ease-in-out infinite;
    transition: color 0.2s ease;
}

@keyframes gold-pulse {
    0%, 100% { color: inherit; }
    50% { color: #f0b632; }
}
</style>

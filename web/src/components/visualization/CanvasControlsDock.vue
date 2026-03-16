<script setup lang="ts">
import {
    Maximize2,
    Pencil,
    Sigma,
    Upload,
    Eye,
    EyeOff,
    ImageIcon,
} from "lucide-vue-next";
import { Tooltip } from "@/components/ui/tooltip";

const props = defineProps<{
    isEditing: boolean;
    showImageOverlay: boolean;
    showGhost: boolean;
    showEquation: boolean;
    hasData: boolean;
    hasContour: boolean;
    publishing: boolean;
}>();

defineEmits<{
    toggleEdit: [];
    toggleFullscreen: [];
    toggleEquation: [];
    toggleImageOverlay: [];
    toggleGhost: [];
    publish: [];
}>();
</script>

<template>
    <div class="controls-dock">
        <template v-if="!isEditing">
            <!-- Image overlay -->
            <Tooltip text="Image overlay" side="bottom">
                <button class="dock-icon-btn" :class="{ 'is-active': showImageOverlay }" @click="$emit('toggleImageOverlay')">
                    <ImageIcon class="h-4.5 w-4.5" />
                </button>
            </Tooltip>
            <!-- Contour trace -->
            <Tooltip text="Contour trace" side="bottom">
                <button class="dock-icon-btn" :class="{ 'is-active': showGhost }" @click="$emit('toggleGhost')">
                    <component :is="showGhost ? Eye : EyeOff" class="h-4.5 w-4.5" />
                </button>
            </Tooltip>

            <div class="dock-separator" />

            <!-- Publish -->
            <Tooltip v-if="hasContour" text="Publish to Gallery" side="bottom">
                <button class="dock-icon-btn" :class="{ 'is-active': publishing }" @click="$emit('publish')">
                    <Upload class="h-4.5 w-4.5" :class="{ 'animate-pulse': publishing }" />
                </button>
            </Tooltip>
            <!-- Equation -->
            <Tooltip v-if="hasData" text="Equation" side="bottom">
                <button class="dock-icon-btn" :class="{ 'is-active': showEquation }" @click="$emit('toggleEquation')">
                    <Sigma class="h-4.5 w-4.5" />
                </button>
            </Tooltip>

            <div class="dock-separator" />
        </template>

        <!-- Edit (always visible when contour exists) -->
        <Tooltip v-if="hasContour" text="Edit contour" side="bottom">
            <button class="dock-icon-btn" :class="{ 'is-active': isEditing }" @click="$emit('toggleEdit')">
                <Pencil class="h-4.5 w-4.5" />
            </button>
        </Tooltip>
        <!-- Fullscreen -->
        <Tooltip text="Fullscreen" side="bottom">
            <button class="dock-icon-btn" @click="$emit('toggleFullscreen')">
                <Maximize2 class="h-4.5 w-4.5" />
            </button>
        </Tooltip>
    </div>
</template>

<style>
@import "./lib/dock-buttons.css";
</style>

<style scoped>
.controls-dock {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.375rem 0.5rem;
    border-radius: 0.75rem;
    background: hsl(var(--card) / 0.82);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid hsl(var(--border) / 0.5);
    box-shadow: 0 2px 8px hsl(var(--foreground) / 0.08);
}

.controls-dock .dock-icon-btn {
    width: 2.25rem;
    height: 2.25rem;
}

.controls-dock .dock-separator {
    height: 1.5rem;
    margin: 0 0.125rem;
}
</style>

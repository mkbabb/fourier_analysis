<template>
    <div class="cartoon-card config-card">
        <h3 class="config-card-title">{{ title }}</h3>
        <p class="config-card-desc">{{ description }}</p>

        <div class="config-field">
            <div class="duration-row">
                <label class="config-label">Duration</label>
                <div class="input-with-unit">
                    <input
                        type="number"
                        :value="duration"
                        @change="emitDuration(($event.target as HTMLInputElement).value)"
                        min="50"
                        max="800"
                        step="10"
                        class="num-input fira-code"
                    />
                    <span class="input-unit fira-code">ms</span>
                </div>
                <input
                    type="range"
                    :value="duration"
                    @input="$emit('update:duration', Number(($event.target as HTMLInputElement).value))"
                    min="50"
                    max="800"
                    step="10"
                    class="styled-slider"
                    :style="sliderStyle(duration, 50, 800, sliderColor ?? 'hsl(var(--accent-red))')"
                />
            </div>
        </div>

        <div class="config-field">
            <label class="config-label">Easing</label>
            <Select :model-value="easing" @update:model-value="$emit('update:easing', String($event))">
                <SelectTrigger class="w-full">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem
                        v-for="name in easingNames"
                        :key="name"
                        :value="name"
                    >
                        <span class="flex items-center gap-2">
                            <svg class="easing-preview" viewBox="0 0 40 20">
                                <path
                                    :d="easingCurvePath(name)"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="1.5"
                                />
                            </svg>
                            {{ presets[name].label }}
                        </span>
                    </SelectItem>
                </SelectContent>
            </Select>
        </div>
    </div>
</template>

<script setup lang="ts">
import {
    Select,
    SelectTrigger,
    SelectContent,
    SelectItem,
    SelectValue,
} from "@/components/ui/select";
import {
    EASING_PRESETS,
    EASING_PRESET_NAMES,
    easingCurvePath,
    sliderStyle,
} from "@/composables/useMorphConfig";

const props = defineProps<{
    title: string;
    description: string;
    duration: number;
    easing: string;
    sliderColor?: string;
}>();

const emit = defineEmits<{
    "update:duration": [value: number];
    "update:easing": [value: string];
}>();

function emitDuration(raw: string) {
    const v = Math.max(50, Math.min(800, Math.round(Number(raw) || 50)));
    emit("update:duration", v);
}

const presets = EASING_PRESETS;
const easingNames = EASING_PRESET_NAMES;
</script>

<style scoped>
.config-card {
    padding: 1rem 1.25rem;
}

.config-card-title {
    font-family: var(--font-serif);
    font-size: 1rem;
    font-weight: 400;
    color: hsl(var(--foreground));
    margin-bottom: 0.125rem;
}

.config-card-desc {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
    margin-bottom: 0.875rem;
}

.config-field {
    margin-bottom: 0.75rem;
}

.config-field:last-child {
    margin-bottom: 0;
}

.duration-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.config-label {
    display: block;
    font-size: 0.8125rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    margin-bottom: 0.375rem;
}

.duration-row .config-label {
    margin-bottom: 0;
    white-space: nowrap;
}

.input-with-unit {
    display: flex;
    align-items: center;
    gap: 0.125rem;
}

.num-input {
    width: 3.5rem;
    padding: 0.125rem 0.375rem;
    border: 1.5px solid hsl(var(--foreground) / 0.15);
    border-radius: 0.375rem;
    background: hsl(var(--background));
    color: hsl(var(--foreground));
    font-size: 0.8125rem;
    font-weight: 600;
    text-align: right;
    outline: none;
    transition: border-color 0.15s ease;
    -moz-appearance: textfield;
}

.num-input::-webkit-inner-spin-button,
.num-input::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

.num-input:focus {
    border-color: hsl(var(--accent-red));
    box-shadow: 0 0 0 2px hsl(var(--accent-red) / 0.12);
}

.input-unit {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
}

.easing-preview {
    width: 40px;
    height: 20px;
    flex-shrink: 0;
}

/* MorphPhaseConfig slider overrides — smaller thumb */
.styled-slider {
    flex: 1;
}

.styled-slider::-webkit-slider-thumb {
    width: 20px;
    height: 20px;
}

.styled-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
}
</style>

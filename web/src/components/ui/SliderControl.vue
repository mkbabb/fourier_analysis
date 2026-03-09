<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
    label: string;
    modelValue: number;
    min: number;
    max: number;
    step: number;
    color: string;
    /** Format the display value (default: raw number) */
    formatValue?: (v: number) => string;
}>();

const emit = defineEmits<{
    (e: "update:modelValue", v: number): void;
}>();

function clamp(v: number, lo: number, hi: number): number {
    return Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : lo;
}

function onInput(e: Event) {
    emit("update:modelValue", clamp(parseFloat((e.target as HTMLInputElement).value), props.min, props.max));
}

const progress = computed(() => ((props.modelValue - props.min) / (props.max - props.min)) * 100);
const displayValue = computed(() => props.formatValue ? props.formatValue(props.modelValue) : String(props.modelValue));
const isNumericDisplay = computed(() => !Number.isNaN(Number(displayValue.value)));
</script>

<template>
    <div class="slider-control">
        <label class="slider-label">
            <span><slot>{{ label }}</slot></span>
            <input
                :type="isNumericDisplay ? 'number' : 'text'"
                class="inline-number fira-code"
                :value="displayValue"
                :min="isNumericDisplay ? min : undefined"
                :max="isNumericDisplay ? max : undefined"
                :step="isNumericDisplay ? step : undefined"
                @input="onInput"
            />
        </label>
        <input
            :value="modelValue"
            @input="onInput"
            type="range"
            :min="min"
            :max="max"
            :step="step"
            class="styled-slider w-full"
            :style="{ '--progress': progress + '%', '--slider-color': color }"
        />
    </div>
</template>

<style scoped>
.slider-control {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.slider-label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.75rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
}

.inline-number {
    width: 2.75rem;
    text-align: right;
    background: transparent;
    border: none;
    border-bottom: 1px solid transparent;
    color: hsl(var(--foreground));
    font-size: inherit;
    padding: 0;
    outline: none;
    -moz-appearance: textfield;
    transition: border-color 0.15s;
}
.inline-number:hover,
.inline-number:focus {
    border-bottom-color: hsl(var(--foreground) / 0.3);
}
.inline-number::-webkit-inner-spin-button,
.inline-number::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
</style>

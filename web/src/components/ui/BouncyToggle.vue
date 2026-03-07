<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from "vue";

export interface ToggleOption {
    label: string;
    value: string;
}

const props = defineProps<{
    options: ToggleOption[];
    modelValue: string;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: string];
}>();

const containerRef = ref<HTMLElement>();
const buttonRefs = ref<HTMLElement[]>([]);
const sliderStyle = ref({ width: "0px", transform: "translateX(0px)" });

function updateSlider(animate = true) {
    const idx = props.options.findIndex((o) => o.value === props.modelValue);
    if (idx < 0 || !buttonRefs.value[idx]) return;
    const btn = buttonRefs.value[idx];
    sliderStyle.value = {
        width: `${btn.offsetWidth}px`,
        transform: `translateX(${btn.offsetLeft}px)`,
    };
}

function select(value: string, idx: number) {
    const btn = buttonRefs.value[idx];
    if (btn) {
        btn.animate(
            [
                { transform: "scale(1)" },
                { transform: "scale(0.93)", offset: 0.25 },
                { transform: "scale(1.02)", offset: 0.7 },
                { transform: "scale(1)" },
            ],
            { duration: 300, easing: "ease-out" },
        );
    }
    emit("update:modelValue", value);
}

let ro: ResizeObserver | null = null;

onMounted(() => {
    updateSlider(false);
    if (containerRef.value) {
        ro = new ResizeObserver(() => updateSlider(false));
        ro.observe(containerRef.value);
    }
});

onBeforeUnmount(() => {
    ro?.disconnect();
});

watch(() => props.modelValue, () => nextTick(() => updateSlider(true)));
</script>

<template>
    <div ref="containerRef" class="bouncy-toggle">
        <div class="bouncy-slider" :style="sliderStyle" />
        <button
            v-for="(option, idx) in options"
            :key="option.value"
            :ref="(el) => { if (el) buttonRefs[idx] = el as HTMLElement }"
            class="bouncy-btn"
            :class="{ 'is-active': modelValue === option.value }"
            @click="select(option.value, idx)"
        >
            {{ option.label }}
        </button>
    </div>
</template>

<style scoped>
.bouncy-toggle {
    position: relative;
    display: inline-grid;
    grid-auto-columns: 1fr;
    grid-auto-flow: column;
    padding: 0.25rem;
    border-radius: 0.5rem;
    background: hsl(var(--muted) / 0.5);
}

.bouncy-slider {
    position: absolute;
    inset-block: 0.25rem;
    border-radius: 0.375rem;
    background: hsl(var(--background));
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 1px hsl(var(--border) / 0.3);
    transition:
        transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
        width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    z-index: 0;
}

.bouncy-btn {
    position: relative;
    z-index: 1;
    padding: 0.375rem 0.875rem;
    border-radius: 0.375rem;
    border: none;
    background: none;
    font-family: "CMU Serif", "Computer Modern", Georgia, serif;
    font-size: 0.8125rem;
    font-weight: 700;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    transition: color 0.2s ease;
    white-space: nowrap;
    text-align: center;
    -webkit-tap-highlight-color: transparent;
}

.bouncy-btn:hover:not(.is-active) {
    color: hsl(var(--foreground) / 0.7);
}

.bouncy-btn.is-active {
    color: hsl(var(--foreground));
}
</style>

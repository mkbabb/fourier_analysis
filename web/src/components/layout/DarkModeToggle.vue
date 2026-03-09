<template>
    <button
        class="sun-moon-toggle"
        @click="handleToggle"
        :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    >
        <FourierMorphSvg
            :path="morph.currentPath.value"
            :stroke-width="14"
            :stroke-color="strokeColor"
            view-box="0 0 200 200"
        />
    </button>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import FourierMorphSvg from "@/components/decorative/FourierMorphSvg.vue";
import { useFourierMorph } from "@/composables/useFourierMorph";
import { prepareFourierShape } from "@/lib/svg-fourier";

import sunData from "@/assets/fourier-paths/sun.json";
import moonData from "@/assets/fourier-paths/moon.json";

const sunShape = prepareFourierShape(sunData as any);
const moonShape = prepareFourierShape(moonData as any);

// Sun: warm orange   Moon: legendre purple
const SUN_COLOR = [232, 136, 69] as const;   // #E88845
const MOON_COLOR = [192, 132, 252] as const; // #c084fc — matches VIZ_COLORS.legendre

const isDark = ref(false);
/** true when morphing toward dark (moon), false when morphing toward light (sun) */
const morphingToDark = ref(false);

const morph = useFourierMorph();

function lerpColor(a: readonly number[], b: readonly number[], t: number): string {
    const r = Math.round(a[0] + (b[0] - a[0]) * t);
    const g = Math.round(a[1] + (b[1] - a[1]) * t);
    const bl = Math.round(a[2] + (b[2] - a[2]) * t);
    return `rgb(${r},${g},${bl})`;
}

const strokeColor = computed(() => {
    if (morph.phase.value === "idle") {
        return isDark.value
            ? lerpColor(SUN_COLOR, MOON_COLOR, 1)
            : lerpColor(SUN_COLOR, MOON_COLOR, 0);
    }
    const [from, to] = morphingToDark.value
        ? [SUN_COLOR, MOON_COLOR]
        : [MOON_COLOR, SUN_COLOR];
    return lerpColor(from, to, morph.morphProgress.value);
});

onMounted(() => {
    isDark.value = document.documentElement.classList.contains("dark");
    morph.setShape(isDark.value ? moonShape : sunShape);
});

async function handleToggle() {
    if (morph.phase.value !== "idle") return;

    const from = isDark.value ? moonShape : sunShape;
    const to = isDark.value ? sunShape : moonShape;

    morphingToDark.value = !isDark.value;
    isDark.value = !isDark.value;
    document.documentElement.classList.toggle("dark", isDark.value);
    localStorage.setItem("theme", isDark.value ? "dark" : "light");

    await morph.morphTo(from, to);
}
</script>

<style scoped>
.sun-moon-toggle {
    position: relative;
    width: var(--toggle-size, 5rem);
    height: var(--toggle-size, 5rem);
    cursor: pointer;
    border: 0;
    padding: 0;
    border-radius: 50%;
    background: transparent;
    transition: transform 200ms ease;
    flex-shrink: 0;
}

.sun-moon-toggle:hover {
    outline: none;
    transform: scale(1.12);
}

.sun-moon-toggle:focus {
    outline: none;
}

.sun-moon-toggle:focus-visible {
    outline: 2px solid var(--color-ring);
    outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    .sun-moon-toggle {
        transition: none;
    }
}
</style>

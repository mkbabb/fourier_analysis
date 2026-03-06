<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";

const svgRef = ref<SVGSVGElement | null>(null);
let interval: ReturnType<typeof setInterval> | null = null;

const reducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const offsets = [0, 0.002, -0.001, 0.003, -0.002, 0.001];
const baseFreq = 0.015;
let idx = 0;

function startBoil() {
    if (reducedMotion || !svgRef.value) return;
    const turbEl = svgRef.value.querySelector("#title-boil feTurbulence") as SVGFETurbulenceElement | null;
    if (!turbEl) return;

    interval = setInterval(() => {
        const offset = offsets[idx % offsets.length];
        const freq = Math.round((baseFreq + offset) * 10000) / 10000;
        turbEl.setAttribute("baseFrequency", String(freq));
        idx++;
    }, 150);
}

onMounted(() => {
    requestAnimationFrame(() => startBoil());
});

onUnmounted(() => {
    if (interval) clearInterval(interval);
});
</script>

<template>
    <svg
        ref="svgRef"
        width="0"
        height="0"
        style="position: absolute; pointer-events: none"
        aria-hidden="true"
    >
        <defs>
            <!-- Title boil: subtle wobble for the main heading -->
            <filter
                id="title-boil"
                filterUnits="objectBoundingBox"
                x="-5%"
                y="-5%"
                width="110%"
                height="110%"
                color-interpolation-filters="sRGB"
            >
                <feTurbulence
                    type="turbulence"
                    baseFrequency="0.015"
                    numOctaves="2"
                    result="turbulence"
                    stitchTiles="noStitch"
                />
                <feDisplacementMap
                    in="SourceGraphic"
                    in2="turbulence"
                    scale="3"
                    xChannelSelector="R"
                    yChannelSelector="G"
                />
            </filter>

            <!-- Paper grain: static noise overlay for cards -->
            <filter id="paper-grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
                <feTurbulence
                    type="fractalNoise"
                    baseFrequency="0.8"
                    numOctaves="3"
                    stitchTiles="stitch"
                    result="grain"
                />
                <feColorMatrix
                    type="saturate"
                    values="0"
                    result="desaturated"
                />
                <feBlend
                    in="SourceGraphic"
                    in2="desaturated"
                    mode="multiply"
                />
            </filter>
        </defs>
    </svg>
</template>

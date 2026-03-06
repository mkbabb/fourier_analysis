<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";

const svgRef = ref<SVGSVGElement | null>(null);
let boilInterval: ReturnType<typeof setInterval> | null = null;

const reducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Boil config — inspired by CSC411 pencil-boil system.
   Cycles through small baseFrequency offsets at ~6.7fps
   to create a hand-drawn wobble effect on the title. */
const boilOffsets = [0, 0.002, -0.001, 0.003, -0.002, 0.001, -0.003, 0.001];
const baseFreq = 0.015;
let boilIdx = 0;

function startBoil() {
    if (reducedMotion || !svgRef.value) return;
    const turbEl = svgRef.value.querySelector(
        "#title-boil feTurbulence",
    ) as SVGFETurbulenceElement | null;
    if (!turbEl) return;

    boilInterval = setInterval(() => {
        const offset = boilOffsets[boilIdx % boilOffsets.length];
        const freq = Math.round((baseFreq + offset) * 10000) / 10000;
        turbEl.setAttribute("baseFrequency", String(freq));
        boilIdx++;
    }, 150);
}

onMounted(() => {
    requestAnimationFrame(() => startBoil());
});

onUnmounted(() => {
    if (boilInterval) clearInterval(boilInterval);
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
            <!-- Title boil: animated wobble displacement for main heading.
                 JS oscillates baseFrequency at ~6.7fps for hand-drawn feel. -->
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

            <!-- Paper grain: static fractal noise overlay for theorem/card elements.
                 Multiply blend adds subtle paper fiber texture. -->
            <filter
                id="paper-grain"
                x="0"
                y="0"
                width="100%"
                height="100%"
                color-interpolation-filters="sRGB"
            >
                <feTurbulence
                    type="fractalNoise"
                    baseFrequency="0.65"
                    numOctaves="4"
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

            <!-- Gentle static grain for canvas/visualization area -->
            <filter
                id="canvas-grain"
                x="0"
                y="0"
                width="100%"
                height="100%"
                color-interpolation-filters="sRGB"
            >
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
                    result="grained"
                />
            </filter>
        </defs>
    </svg>
</template>

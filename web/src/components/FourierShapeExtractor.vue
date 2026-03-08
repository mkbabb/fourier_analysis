<template>
    <div class="extractor-page" style="padding: 2rem">
        <h1>Shape Extractor (internal tool)</h1>

        <div style="display: flex; gap: 2rem; margin: 2rem 0">
            <!-- Sun SVG -->
            <div>
                <h2>Sun</h2>
                <svg
                    ref="sunSvgRef"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 200 200"
                    width="200"
                    height="200"
                    style="border: 1px solid #ccc"
                >
                    <g>
                        <!-- Rays -->
                        <polygon
                            :points="sunRayPoints.outerPoly"
                            fill="none"
                            stroke="red"
                            stroke-width="3"
                            stroke-linejoin="round"
                        />
                        <!-- Disc -->
                        <circle
                            cx="100"
                            cy="100"
                            r="48"
                            fill="none"
                            stroke="red"
                            stroke-width="3"
                        />
                        <!-- Golden spiral -->
                        <path
                            d="M100,100 C106,90 118,94 119,106 C121,122 105,130 90,124 C72,115 68,92 80,76 C96,56 126,56 138,76"
                            fill="none"
                            stroke="red"
                            stroke-width="3"
                            stroke-linecap="round"
                        />
                        <!-- Sparkle diamonds -->
                        <polygon
                            :points="sunSparklePoints[0]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <polygon
                            :points="sunSparklePoints[1]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <polygon
                            :points="sunSparklePoints[2]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <!-- Tiny dots -->
                        <circle cx="30" cy="45" r="2" fill="red" />
                        <circle cx="55" cy="170" r="2.5" fill="red" />
                    </g>
                </svg>
            </div>

            <!-- Moon SVG -->
            <div>
                <h2>Moon</h2>
                <svg
                    ref="moonSvgRef"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 200 200"
                    width="200"
                    height="200"
                    style="border: 1px solid #ccc"
                >
                    <g>
                        <!-- Crescent -->
                        <path
                            d="M85,30 C40,40 15,90 35,140 C55,185 115,190 155,150 C120,165 70,145 60,95 C55,65 65,40 85,30 Z"
                            fill="none"
                            stroke="red"
                            stroke-width="3"
                            stroke-linejoin="round"
                        />
                        <!-- Inner stroke detail -->
                        <path
                            d="M75,45 C50,65 45,105 55,135"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                            stroke-linecap="round"
                        />
                        <!-- 5-point polygon stars -->
                        <polygon
                            :points="starPolygonPoints[0]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <polygon
                            :points="starPolygonPoints[1]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <polygon
                            :points="starPolygonPoints[2]"
                            fill="none"
                            stroke="red"
                            stroke-width="2"
                        />
                        <!-- Tiny dot stars -->
                        <circle cx="120" cy="30" r="2" fill="red" />
                        <circle cx="185" cy="35" r="2.5" fill="red" />
                        <circle cx="155" cy="75" r="1.5" fill="red" />
                    </g>
                </svg>
            </div>
        </div>

        <button id="extract-btn" @click="extractAndOutput">
            Extract Shape Contours
        </button>

        <pre
            id="output"
            style="
                margin-top: 1rem;
                max-height: 300px;
                overflow: auto;
                font-size: 0.75rem;
            "
        ></pre>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { generateSunRays, wobbleDiamond, wobbleStarPolygon } from "@mkbabb/pencil-boil";
import { extractContours } from "@/lib/svg-contours";

const sunSvgRef = ref<SVGSVGElement | null>(null);
const moonSvgRef = ref<SVGSVGElement | null>(null);

// Use seed 42 for canonical shapes (first frame = seed * 100 + 42 = 42)
const sunRayPoints = computed(() => generateSunRays(42));

const starPolygonPoints = computed(() => [
    wobbleStarPolygon(160, 20, 12, 5, 1),
    wobbleStarPolygon(135, 50, 10, 4, 2),
    wobbleStarPolygon(175, 65, 9, 3.5, 3),
]);

const sunSparklePoints = computed(() => [
    wobbleDiamond(35, 40, 6, 10, 10),
    wobbleDiamond(170, 45, 5, 8, 20),
    wobbleDiamond(55, 170, 5, 9, 30),
]);

function extractAndOutput() {
    if (!sunSvgRef.value || !moonSvgRef.value) return;

    const sunContours = extractContours(sunSvgRef.value, 128);
    const moonContours = extractContours(moonSvgRef.value, 128);

    const output = {
        sun: sunContours,
        moon: moonContours,
    };

    const el = document.getElementById("output");
    if (el) {
        el.textContent = JSON.stringify(output);
        // Also put it on window for Playwright to access
        (window as any).__fourierShapeData = output;
    }
}

// Auto-extract on mount
onMounted(() => {
    // Small delay to ensure SVGs are rendered
    setTimeout(() => {
        extractAndOutput();
    }, 200);
});
</script>

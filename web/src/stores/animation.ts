import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import { Animation } from "@mkbabb/keyframes.js";
import {
    easeInOutSine,
    easeInOutCubic,
    easeInOutQuad,
    easeInOutExpo,
    easeInOutCirc,
} from "@mkbabb/value.js";

// ── Easing catalog ──
// Each entry: [label, fn(t) → t, description]
export type EasingName = "linear" | "sine" | "quad" | "cubic" | "circ" | "expo";

export const EASING_OPTIONS: Record<EasingName, {
    label: string;
    fn: (t: number) => number;
    description: string;
}> = {
    linear:  { label: "Linear",      fn: (t) => t,          description: "Constant rate" },
    sine:    { label: "Sine",        fn: easeInOutSine,     description: "Gentle ebb and flow" },
    quad:    { label: "Quadratic",   fn: easeInOutQuad,     description: "Smooth acceleration" },
    cubic:   { label: "Cubic",       fn: easeInOutCubic,    description: "Pronounced ease" },
    circ:    { label: "Circular",    fn: easeInOutCirc,     description: "Snappy midpoint" },
    expo:    { label: "Exponential", fn: easeInOutExpo,     description: "Dramatic slow-fast-slow" },
};

/** Generate an SVG path `d` attribute by sampling an easing function. */
function generateCurveSVGPath(fn: (t: number) => number, n = 32): string {
    const pts: string[] = [];
    for (let i = 0; i <= n; i++) {
        const t = i / n;
        const v = fn(t);
        pts.push(`${t.toFixed(3)},${(1 - v).toFixed(3)}`);
    }
    return `M ${pts.join(" L ")}`;
}

const _svgCache = new Map<EasingName, string>();

/** Get the cached SVG path for an easing curve. */
export function getEasingSVGPath(name: EasingName): string {
    let p = _svgCache.get(name);
    if (!p) {
        p = generateCurveSVGPath(EASING_OPTIONS[name].fn);
        _svgCache.set(name, p);
    }
    return p;
}

export const useAnimationStore = defineStore("animation", () => {
    const t = ref(0);
    const playing = ref(false);
    const speed = ref(1);
    const duration = ref(20000); // ms per full cycle
    const easing = ref<EasingName>("sine");

    // Globally eased t — one smooth curve, no per-segment stutter
    const easedT = computed(() => {
        const fn = EASING_OPTIONS[easing.value]?.fn ?? ((x: number) => x);
        return fn(t.value);
    });

    let anim: Animation | null = null;
    let rafId: number | null = null;

    function createAnim(): Animation {
        if (anim) {
            anim.stop();
        }
        stopRAF();

        const a = new Animation({
            duration: duration.value / speed.value,
            iterationCount: 1,
            timingFunction: "linear",
            fillMode: "forwards",
            useWAAPI: false,
        });

        a.addFrame("0%", { t: "0px" }, (_vars: any, time: number) => {
            t.value = Math.min(time / a.options.duration, 1);
        });
        a.addFrame("100%", { t: "1px" });
        a.parse();

        anim = a;
        return a;
    }

    // Manual rAF loop with alternate (ping-pong)
    function startLoop() {
        let startTime: number | null = null;
        const dur = duration.value / speed.value;

        function tick(now: number) {
            if (!playing.value) return;
            if (startTime === null) startTime = now - t.value * dur;

            const elapsed = now - startTime;
            // Which cycle are we in? Even = forward, odd = reverse
            const cycle = Math.floor(elapsed / dur);
            const frac = (elapsed % dur) / dur;
            t.value = cycle % 2 === 0 ? frac : 1 - frac;

            rafId = requestAnimationFrame(tick);
        }

        rafId = requestAnimationFrame(tick);
    }

    function stopRAF() {
        if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
    }

    function play() {
        if (playing.value) return;
        playing.value = true;
        startLoop();
    }

    function pause() {
        if (!playing.value) return;
        playing.value = false;
        stopRAF();
    }

    function toggle() {
        if (playing.value) pause();
        else play();
    }

    // Scrubbing state — pauses the rAF loop while the user drags
    const scrubbing = ref(false);

    function startScrub() {
        scrubbing.value = true;
        stopRAF();
    }

    function endScrub() {
        scrubbing.value = false;
        if (playing.value) {
            startLoop();
        }
    }

    function seek(normalizedT: number) {
        t.value = Math.max(0, Math.min(1, normalizedT));
    }

    function reset() {
        pause();
        t.value = 0;
    }

    // Restart loop when speed changes mid-play
    watch(speed, () => {
        if (playing.value) {
            stopRAF();
            startLoop();
        }
    });

    return { t, easedT, playing, speed, duration, easing, scrubbing, play, pause, toggle, seek, startScrub, endScrub, reset };
});

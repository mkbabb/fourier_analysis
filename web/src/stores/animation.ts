import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { Animation } from "@mkbabb/keyframes.js";

export const useAnimationStore = defineStore("animation", () => {
    const t = ref(0);
    const playing = ref(false);
    const speed = ref(1);
    const duration = ref(30000); // ms per full cycle

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

    // Manual rAF loop for infinite cycling
    function startLoop() {
        let startTime: number | null = null;
        const dur = duration.value / speed.value;

        function tick(now: number) {
            if (!playing.value) return;
            if (startTime === null) startTime = now - t.value * dur;

            const elapsed = now - startTime;
            t.value = (elapsed % dur) / dur;

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

    return { t, playing, speed, duration, play, pause, toggle, seek, reset };
});

import { defineStore } from "pinia";
import { ref } from "vue";

export const useAnimationStore = defineStore("animation", () => {
    const t = ref(0);
    const playing = ref(false);
    const speed = ref(1);
    const duration = ref(30000); // ms

    let startTime = 0;
    let rafId: number | null = null;

    function tick(timestamp: number) {
        if (!playing.value) return;
        const elapsed = (timestamp - startTime) * speed.value;
        t.value = (elapsed % duration.value) / duration.value;
        rafId = requestAnimationFrame(tick);
    }

    function play() {
        if (playing.value) return;
        playing.value = true;
        startTime = performance.now() - (t.value * duration.value) / speed.value;
        rafId = requestAnimationFrame(tick);
    }

    function pause() {
        playing.value = false;
        if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
    }

    function toggle() {
        if (playing.value) pause();
        else play();
    }

    function seek(normalizedT: number) {
        t.value = Math.max(0, Math.min(1, normalizedT));
        startTime = performance.now() - (t.value * duration.value) / speed.value;
    }

    function reset() {
        pause();
        t.value = 0;
    }

    return { t, playing, speed, duration, play, pause, toggle, seek, reset };
});

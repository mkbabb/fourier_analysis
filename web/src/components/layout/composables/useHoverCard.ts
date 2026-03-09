import { ref, onUnmounted } from "vue";

const canHover = typeof window !== "undefined"
    && window.matchMedia("(hover: hover)").matches;

export function useHoverCard(closeDelay = 150) {
    const isOpen = ref(false);
    let closeTimer: ReturnType<typeof setTimeout> | null = null;

    onUnmounted(() => {
        if (closeTimer) clearTimeout(closeTimer);
    });

    function toggle() {
        isOpen.value = !isOpen.value;
    }

    function close() {
        isOpen.value = false;
    }

    function onHoverEnter() {
        if (!canHover) return;
        if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
        }
        isOpen.value = true;
    }

    function onHoverLeave() {
        if (!canHover) return;
        closeTimer = setTimeout(() => {
            isOpen.value = false;
            closeTimer = null;
        }, closeDelay);
    }

    return { isOpen, toggle, close, onHoverEnter, onHoverLeave };
}

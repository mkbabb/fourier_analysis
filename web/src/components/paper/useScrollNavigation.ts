import { reactive, nextTick } from "vue";
import type { Ref } from "vue";

export interface ScrollNavigationOptions {
    scrollContainer: Ref<HTMLElement | null>;
    contentStartOffsetPx: Ref<number>;
    activeId: Ref<string | null>;
    ensureTargetWindow: (id: string) => void;
    getOffsetFor: (id: string) => number | null;
    recalculate: () => void;
}

export function useScrollNavigation(opts: ScrollNavigationOptions) {
    const TELEPORT_THRESHOLD = 1400;
    const MAX_STACK = 20;
    const MIN_OVERLAY_VISIBLE_MS = 90;
    const navStack = reactive<string[]>([]);
    let isBackNavigation = false;

    function getScrollOffset(): number {
        const bar = document.querySelector(".floating-toc-bar") as HTMLElement | null;
        if (bar) return bar.offsetHeight + 8;
        return 16;
    }

    function computeAbsoluteTargetTop(
        scroller: HTMLElement,
        id: string,
    ): number | null {
        const layoutOffset = opts.getOffsetFor(id);
        if (layoutOffset == null) return null;

        const target = document.getElementById(id);
        const absoluteTop = target
            ? target.getBoundingClientRect().top -
              scroller.getBoundingClientRect().top +
              scroller.scrollTop
            : opts.contentStartOffsetPx.value + layoutOffset;

        return Math.max(0, absoluteTop - getScrollOffset());
    }

    function withTeleportOverlay(
        scroller: HTMLElement,
        run: (finish: () => void) => void,
    ) {
        const overlay = scroller.querySelector(".teleport-overlay") as HTMLElement | null;
        if (!overlay) {
            run(() => {
                opts.recalculate();
            });
            return;
        }

        let finished = false;
        const shownAt = performance.now();
        const finish = () => {
            if (finished) return;
            finished = true;
            const finalize = () => {
                opts.recalculate();
                requestAnimationFrame(() => {
                    overlay.style.opacity = "0";
                    overlay.style.pointerEvents = "none";
                });
            };
            const remaining = Math.max(0, MIN_OVERLAY_VISIBLE_MS - (performance.now() - shownAt));
            if (remaining === 0) {
                finalize();
                return;
            }
            window.setTimeout(finalize, remaining);
        };

        overlay.style.pointerEvents = "auto";
        overlay.style.opacity = "1";

        // Let the fade paint for a frame before the jump starts.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                run(finish);
            });
        });
    }

    function teleportTo(scroller: HTMLElement, id: string) {
        const jumpUntilStable = (onDone: () => void) => {
            let lastTop = -1;
            let stableFrames = 0;
            let frames = 0;

            const correct = () => {
                const targetTop = computeAbsoluteTargetTop(scroller, id);
                if (targetTop == null) {
                    if (frames++ < 30) requestAnimationFrame(correct);
                    else onDone();
                    return;
                }

                scroller.scrollTo({ top: targetTop, behavior: "instant" });
                opts.recalculate();

                if (Math.abs(targetTop - lastTop) < 2) {
                    stableFrames += 1;
                } else {
                    stableFrames = 0;
                }
                lastTop = targetTop;

                if (stableFrames >= 3 || frames++ >= 24) {
                    onDone();
                    return;
                }
                requestAnimationFrame(correct);
            };

            correct();
        };

        withTeleportOverlay(scroller, (finish) => {
            jumpUntilStable(() => {
                finish();
            });
        });
    }

    function performScroll(id: string) {
        const scroller = opts.scrollContainer.value;
        if (!scroller) return;

        opts.ensureTargetWindow(id);

        let attempts = 0;
        function tryNavigate() {
            const container = opts.scrollContainer.value;
            if (!container) return;

            const targetTop = computeAbsoluteTargetTop(container, id);
            if (targetTop == null) {
                if (attempts++ < 60) requestAnimationFrame(tryNavigate);
                return;
            }

            const distance = Math.abs(targetTop - container.scrollTop);
            if (distance < TELEPORT_THRESHOLD) {
                container.scrollTo({ top: targetTop, behavior: "smooth" });
                return;
            }

            teleportTo(container, id);
        }

        nextTick(() => requestAnimationFrame(tryNavigate));
    }

    function navigateTo(id: string) {
        if (!isBackNavigation && opts.activeId.value && opts.activeId.value !== id) {
            navStack.push(opts.activeId.value);
            if (navStack.length > MAX_STACK) navStack.shift();
        }
        performScroll(id);
    }

    function navigateBack() {
        if (navStack.length === 0) return;
        isBackNavigation = true;
        const prev = navStack.pop()!;
        performScroll(prev);
        setTimeout(() => {
            isBackNavigation = false;
        }, 500);
    }

    function scrollToTop() {
        const scroller = opts.scrollContainer.value;
        if (!scroller) return;
        if (scroller.scrollTop > TELEPORT_THRESHOLD) {
            if (!scroller.querySelector(".teleport-overlay")) {
                scroller.scrollTo({ top: 0, behavior: "instant" });
                return;
            }

            withTeleportOverlay(scroller, (finish) => {
                scroller.scrollTo({ top: 0, behavior: "instant" });
                finish();
            });
            return;
        }
        scroller.scrollTo({ top: 0, behavior: "smooth" });
    }

    return { navigateTo, navigateBack, scrollToTop, navStack };
}

import { ref, watch } from "vue";
import { useWorkspaceStore } from "@/stores/workspace";

const VIEW_STATE_KEY = "fourier_visualizer_view_state";

function loadViewState(): { editing?: boolean; overlay?: boolean } {
    try {
        return JSON.parse(localStorage.getItem(VIEW_STATE_KEY) ?? "{}");
    } catch {
        return {};
    }
}

export function useViewState() {
    const store = useWorkspaceStore();
    const saved = loadViewState();

    const isEditing = ref(false);
    const showGhost = ref(true);
    const showImageOverlay = ref(typeof saved.overlay === "boolean" ? saved.overlay : false);

    // Restore editing once contour is available
    if (saved.editing) {
        let restored = false;
        watch(
            () => store.contour,
            (contour) => {
                if (contour && !restored) {
                    restored = true;
                    setTimeout(() => { isEditing.value = true; }, 300);
                }
            },
            { immediate: true },
        );
    }

    // Auto-exit editing if contour disappears
    watch(() => store.contour, (c) => {
        if (!c && isEditing.value) isEditing.value = false;
    });

    watch([isEditing, showImageOverlay], () => {
        localStorage.setItem(VIEW_STATE_KEY, JSON.stringify({
            editing: isEditing.value,
            overlay: showImageOverlay.value,
        }));
    });

    return { isEditing, showGhost, showImageOverlay };
}

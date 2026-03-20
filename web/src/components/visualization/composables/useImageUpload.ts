import { ref, onUnmounted } from "vue";

const IMAGE_EXTENSIONS = new Set([
    "png", "jpg", "jpeg", "gif", "bmp", "webp", "svg", "tiff", "tif",
]);

/** Safari-safe image detection: fall back to extension when MIME type is empty. */
function isImageFile(file: File): boolean {
    if (file.type.startsWith("image/")) return true;
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    return IMAGE_EXTENSIONS.has(ext);
}

export function useImageUpload(onFile: (file: File) => void) {
    const isDragging = ref(false);
    const preview = ref<string | null>(null);

    // Track active FileReader so we can abort on new selection or unmount
    let activeReader: FileReader | null = null;

    onUnmounted(() => {
        if (activeReader && activeReader.readyState === FileReader.LOADING) {
            activeReader.abort();
        }
        activeReader = null;
    });

    // Counter-based drag tracking to handle child element enter/leave events
    let dragCounter = 0;

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        dragCounter = 0;
        isDragging.value = false;
        const file = e.dataTransfer?.files[0];
        if (file && isImageFile(file)) {
            setPreview(file);
            onFile(file);
        }
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
        // Safari fallback: dragenter may not fire reliably
        if (!isDragging.value && dragCounter === 0) {
            dragCounter = 1;
            isDragging.value = true;
        }
    }

    function handleDragEnter(e: DragEvent) {
        e.preventDefault();
        dragCounter++;
        isDragging.value = true;
    }

    function handleDragLeave(e: DragEvent) {
        e.preventDefault();
        dragCounter--;
        if (dragCounter <= 0) {
            dragCounter = 0;
            isDragging.value = false;
        }
    }

    function handleFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (file && isImageFile(file)) {
            setPreview(file);
            onFile(file);
        }
    }

    function setPreview(file: File) {
        // Abort any in-progress read
        if (activeReader && activeReader.readyState === FileReader.LOADING) {
            activeReader.abort();
        }
        const reader = new FileReader();
        activeReader = reader;
        reader.onload = (e) => {
            preview.value = e.target?.result as string;
        };
        reader.readAsDataURL(file);
    }

    function clearPreview() {
        if (activeReader && activeReader.readyState === FileReader.LOADING) {
            activeReader.abort();
        }
        activeReader = null;
        preview.value = null;
    }

    return {
        isDragging,
        preview,
        clearPreview,
        handleDrop,
        handleDragOver,
        handleDragEnter,
        handleDragLeave,
        handleFileSelect,
    };
}

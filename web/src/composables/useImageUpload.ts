import { ref } from "vue";

export function useImageUpload(onFile: (file: File) => void) {
    const isDragging = ref(false);
    const preview = ref<string | null>(null);

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        isDragging.value = false;
        const file = e.dataTransfer?.files[0];
        if (file && file.type.startsWith("image/")) {
            setPreview(file);
            onFile(file);
        }
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
        isDragging.value = true;
    }

    function handleDragLeave() {
        isDragging.value = false;
    }

    function handleFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (file) {
            setPreview(file);
            onFile(file);
        }
    }

    function setPreview(file: File) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.value = e.target?.result as string;
        };
        reader.readAsDataURL(file);
    }

    return {
        isDragging,
        preview,
        handleDrop,
        handleDragOver,
        handleDragLeave,
        handleFileSelect,
    };
}

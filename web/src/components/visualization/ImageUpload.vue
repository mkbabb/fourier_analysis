<script setup lang="ts">
import { ref } from "vue";
import { useSessionStore } from "@/stores/session";
import { useImageUpload } from "@/composables/useImageUpload";
import { imageUrl } from "@/lib/api";
import { ImagePlus, Upload, Replace } from "lucide-vue-next";

const store = useSessionStore();
const fileInput = ref<HTMLInputElement>();

const { isDragging, preview, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } =
    useImageUpload(async (file: File) => {
        await store.uploadImage(file);
    });

function openFilePicker() {
    fileInput.value?.click();
}
</script>

<template>
    <div class="rounded-xl border border-border bg-card p-4 card-hover">
        <h3 class="fraunces mb-3 text-sm font-semibold tracking-tight flex items-center gap-2">
            <ImagePlus class="h-4 w-4 text-muted-foreground" />
            Image
        </h3>

        <!-- Preview with overlay replace button -->
        <div
            v-if="store.hasImage || preview"
            class="group relative mb-3 overflow-hidden rounded-lg animate-scale-in"
        >
            <img
                :src="preview || (store.slug ? imageUrl(store.slug) : '')"
                alt="Uploaded image"
                class="w-full object-contain transition-all duration-300"
                style="max-height: 200px"
            />
            <div
                class="absolute inset-0 flex items-center justify-center bg-black/0 transition-all duration-200 group-hover:bg-black/30 cursor-pointer"
                @click="openFilePicker"
            >
                <div
                    class="flex items-center gap-1.5 rounded-md bg-background/90 px-3 py-1.5 text-xs font-medium opacity-0 transition-all duration-200 group-hover:opacity-100 shadow-sm backdrop-blur-sm"
                >
                    <Replace class="h-3 w-3" />
                    Replace
                </div>
            </div>
        </div>

        <!-- Drop zone -->
        <div
            class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-all duration-200"
            :class="{
                'border-primary bg-primary/5 scale-[1.01]': isDragging,
                'border-border hover:border-muted-foreground hover:bg-muted/30': !isDragging,
            }"
            @drop="handleDrop"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @click="openFilePicker"
        >
            <Upload
                class="mb-2.5 h-8 w-8 transition-all duration-200"
                :class="{
                    'text-primary': isDragging,
                    'text-muted-foreground': !isDragging,
                }"
            />
            <p class="text-sm font-medium text-muted-foreground">
                {{ store.hasImage ? "Drop to replace" : "Drop an image or click to upload" }}
            </p>
            <p class="mt-1 text-xs text-muted-foreground/60">
                PNG, JPG, SVG up to 10MB
            </p>
        </div>

        <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFileSelect"
        />
    </div>
</template>

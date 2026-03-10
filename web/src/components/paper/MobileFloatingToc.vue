<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from "vue";
import { ChevronDown, ChevronUp } from "lucide-vue-next";
import type { PaperSectionData } from "@/lib/paperContent";

const props = defineProps<{
    sections: PaperSectionData[];
    activeRootId: string | null;
    currentSection: PaperSectionData | null;
    scrollTo: (id: string) => void;
    scrollToTop: () => void;
    renderTitle: (title: string) => string;
    scrollContainer: HTMLElement | null;
}>();

const floatingTocOpen = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

// Lock scroll container when dropdown is open (critical for iOS WebKit)
watch(floatingTocOpen, (open) => {
    if (props.scrollContainer) {
        props.scrollContainer.style.overflow = open ? 'hidden' : '';
    }
});

// Cleanup: restore scroll if component unmounts while open
onUnmounted(() => {
    if (props.scrollContainer) {
        props.scrollContainer.style.overflow = '';
    }
});

function selectSection(id: string) {
    floatingTocOpen.value = false;
    props.scrollTo(id);
}

function handleScrollToTop() {
    floatingTocOpen.value = false;
    props.scrollToTop();
}
</script>

<template>
    <div class="floating-toc lg:hidden">
        <div class="floating-toc-anchor">
            <button class="floating-toc-bar" @click="floatingTocOpen = !floatingTocOpen">
                <span class="floating-toc-section cm-serif">
                    <span class="fira-code text-xs opacity-50">{{ currentSection?.number }}.</span>
                    {{ currentSection?.title }}
                </span>
                <ChevronDown class="floating-toc-chevron" :class="{ 'rotate-180': floatingTocOpen }" />
            </button>
            <Transition name="toc-expand">
                <div
                    v-if="floatingTocOpen"
                    ref="dropdownRef"
                    class="floating-toc-dropdown"
                >
                    <!-- Scroll to top -->
                    <button
                        class="floating-toc-item floating-toc-top cm-serif"
                        @click="handleScrollToTop"
                    >
                        <ChevronUp class="floating-toc-top-icon" />
                        Scroll to top
                    </button>

                    <div class="floating-toc-divider" />

                    <button
                        v-for="(section, si) in sections"
                        :key="section.id"
                        class="floating-toc-item cm-serif"
                        :class="{ 'is-active': activeRootId === section.id }"
                        :style="activeRootId === section.id ? { color: `var(--section-color-${si})` } : {}"
                        @click="selectSection(section.id)"
                    >
                        <span class="fira-code text-xs opacity-50">{{ section.number }}.</span>
                        {{ section.title }}
                    </button>
                </div>
            </Transition>

            <!-- Backdrop to close dropdown on outside tap -->
            <div
                v-if="floatingTocOpen"
                class="floating-toc-backdrop"
                @click="floatingTocOpen = false"
            />
        </div>
    </div>
</template>

<style scoped>
.floating-toc {
    position: sticky;
    top: 0;
    z-index: 20;
    height: 0;
    overflow: visible;
}

.floating-toc-anchor {
    position: relative;
}

.floating-toc-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    width: 100%;
    padding: 0.625rem 1rem;
    background: hsl(var(--background) / 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: none;
    border-bottom: 1px solid hsl(var(--border) / 0.5);
    cursor: pointer;
    text-align: left;
    font-size: 0.875rem;
    font-weight: 500;
    color: hsl(var(--foreground));
    position: relative;
    z-index: 2;
}

.floating-toc-section {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
}

.floating-toc-chevron {
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
    opacity: 0.6;
    transition: transform 0.2s ease;
}
.floating-toc-chevron.rotate-180 {
    opacity: 0.8;
}

.floating-toc-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 2;
    background: hsl(var(--background) / 0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid hsl(var(--border));
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    max-height: 60vh;
    overflow-y: auto;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    touch-action: pan-y;
    padding: 0.5rem;
}

.floating-toc-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1;
}

.floating-toc-top {
    display: flex !important;
    align-items: center;
    gap: 0.375rem;
    color: hsl(var(--muted-foreground) / 0.7) !important;
    font-size: 0.75rem !important;
}

.floating-toc-top-icon {
    width: 0.875rem;
    height: 0.875rem;
    opacity: 0.6;
}

.floating-toc-divider {
    height: 1px;
    background: hsl(var(--border) / 0.5);
    margin: 0.25rem 0.75rem;
}

.floating-toc-item {
    display: block;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    border: none;
    background: none;
    cursor: pointer;
    text-align: left;
    font-size: 0.8125rem;
    color: hsl(var(--muted-foreground));
    transition: all 0.15s;
}

.floating-toc-item:hover,
.floating-toc-item.is-active {
    background: hsl(var(--muted) / 0.5);
    color: hsl(var(--foreground));
}

.floating-toc-item.is-active {
    font-weight: 600;
}

/* ── Transition: toc-expand ──────────────────────────────── */
.toc-expand-enter-active,
.toc-expand-leave-active {
    transition: opacity 0.2s ease,
                transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.toc-expand-enter-from {
    opacity: 0;
    transform: translateY(-0.5rem);
}

.toc-expand-leave-to {
    opacity: 0;
    transform: translateY(-0.5rem);
}
</style>

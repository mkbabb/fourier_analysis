<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Sun, Moon } from "lucide-vue-next";

const isDark = ref(false);

onMounted(() => {
    isDark.value = document.documentElement.classList.contains("dark");
});

function toggle() {
    isDark.value = !isDark.value;
    document.documentElement.classList.toggle("dark", isDark.value);
    localStorage.setItem("theme", isDark.value ? "dark" : "light");
}
</script>

<template>
    <button
        class="relative flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-300 hover:bg-muted btn-press"
        :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        @click="toggle"
    >
        <Transition name="theme-toggle" mode="out-in">
            <Moon v-if="isDark" class="h-4 w-4 text-amber-300" />
            <Sun v-else class="h-4 w-4 text-amber-600" />
        </Transition>
    </button>
</template>

<style scoped>
.theme-toggle-enter-active {
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.theme-toggle-leave-active {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.theme-toggle-enter-from {
    opacity: 0;
    transform: rotate(-90deg) scale(0.5);
}
.theme-toggle-leave-to {
    opacity: 0;
    transform: rotate(90deg) scale(0.5);
}
</style>

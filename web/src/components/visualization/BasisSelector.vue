<script setup lang="ts">
import { ref } from "vue";

const selected = ref<"fourier" | "chebyshev" | "legendre">("fourier");
const mode = ref<"epicycle" | "series" | "comparison">("epicycle");

const emit = defineEmits<{
    (e: "update:basis", basis: string): void;
    (e: "update:mode", mode: string): void;
}>();

const bases = [
    { value: "fourier", label: "Fourier", shortcut: "F" },
    { value: "chebyshev", label: "Chebyshev", shortcut: "C" },
    { value: "legendre", label: "Legendre", shortcut: "L" },
] as const;

const modes = [
    { value: "epicycle", label: "Epicycles" },
    { value: "series", label: "Series" },
    { value: "comparison", label: "Compare" },
] as const;
</script>

<template>
    <div class="rounded-xl border border-border bg-card p-4 card-hover animate-fade-in">
        <h3 class="fraunces mb-3 text-sm font-semibold tracking-tight">Basis & Mode</h3>

        <div class="space-y-3">
            <!-- Basis toggle group -->
            <div>
                <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Basis</label>
                <div class="flex gap-1 rounded-lg bg-muted p-1">
                    <button
                        v-for="b in bases"
                        :key="b.value"
                        class="relative flex-1 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-200"
                        :class="{
                            'bg-background text-foreground shadow-sm': selected === b.value,
                            'text-muted-foreground hover:text-foreground': selected !== b.value,
                        }"
                        @click="selected = b.value; emit('update:basis', b.value)"
                    >
                        {{ b.label }}
                    </button>
                </div>
            </div>

            <!-- Mode toggle group -->
            <div>
                <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Visualization</label>
                <div class="flex gap-1 rounded-lg bg-muted p-1">
                    <button
                        v-for="m in modes"
                        :key="m.value"
                        class="relative flex-1 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-200"
                        :class="{
                            'bg-background text-foreground shadow-sm': mode === m.value,
                            'text-muted-foreground hover:text-foreground': mode !== m.value,
                        }"
                        @click="mode = m.value; emit('update:mode', m.value)"
                    >
                        {{ m.label }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

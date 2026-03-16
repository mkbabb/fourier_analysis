<script setup lang="ts">
import { useToast } from "@/composables/useToast";
import { AlertTriangle, Info, Check, X } from "lucide-vue-next";

const { toasts, dismiss } = useToast();
</script>

<template>
    <Teleport to="body">
        <div class="toast-container" aria-live="polite">
            <TransitionGroup name="toast">
                <div
                    v-for="t in toasts"
                    :key="t.id"
                    class="toast-item"
                    :class="`toast-${t.type}`"
                >
                    <AlertTriangle v-if="t.type === 'error'" class="toast-icon text-amber-500" />
                    <Check v-else-if="t.type === 'success'" class="toast-icon text-green-500" />
                    <Info v-else class="toast-icon text-blue-400" />
                    <p class="toast-msg fira-code">
                        {{ t.message }}
                        <code v-if="t.slug" class="toast-slug">{{ t.slug }}</code>
                    </p>
                    <button class="toast-dismiss" @click="dismiss(t.id)">
                        <X class="h-3.5 w-3.5" />
                    </button>
                </div>
            </TransitionGroup>
        </div>
    </Teleport>
</template>

<style scoped>
@reference "tailwindcss";
.toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: min(24rem, calc(100vw - 2rem));
    pointer-events: none;
}

.toast-item {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.625rem 0.75rem;
    border-radius: 0.625rem;
    border: 1.5px solid hsl(var(--border) / 0.3);
    border-left: 3px solid hsl(var(--border) / 0.3);
    background: hsl(var(--popover) / 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    color: hsl(var(--foreground));
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    pointer-events: auto;
}

.toast-success {
    border-left-color: hsl(142 71% 45%);
}

.toast-error {
    border-color: hsl(var(--destructive) / 0.25);
    border-left-color: hsl(38 92% 50%);
}

.toast-info {
    border-left-color: hsl(217 91% 60%);
}

.toast-icon {
    flex-shrink: 0;
    width: 1rem;
    height: 1rem;
    margin-top: 0.1rem;
}

.toast-msg {
    flex: 1;
    @apply text-sm;
    line-height: 1.4;
    word-break: break-word;
}

.toast-dismiss {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.25rem;
    border: none;
    background: none;
    color: hsl(var(--muted-foreground));
    cursor: pointer;
    border-radius: 0.25rem;
    transition: background 0.15s ease, color 0.15s ease;
}

.toast-dismiss:hover {
    background: hsl(var(--foreground) / 0.1);
    color: hsl(var(--foreground));
}

.toast-slug {
    display: inline;
    font-family: "Fira Code", monospace;
    font-size: 0.8em;
    padding: 0.1em 0.35em;
    border-radius: 0.25rem;
    background: hsl(var(--foreground) / 0.06);
    border: 1px solid hsl(var(--foreground) / 0.1);
    color: hsl(var(--foreground));
}

/* Transitions */
.toast-enter-active {
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-leave-active {
    transition: all 0.2s ease;
}
.toast-enter-from {
    opacity: 0;
    transform: translateX(1rem) scale(0.95);
}
.toast-leave-to {
    opacity: 0;
    transform: translateX(1rem) scale(0.95);
}
.toast-move {
    transition: transform 0.25s ease;
}
</style>

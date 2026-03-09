<script setup lang="ts">
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from 'reka-ui'
import { ref, watch } from 'vue'
import { ChevronRight } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
    title: string;
    subtitle?: string;
    defaultOpen?: boolean;
}>(), {
    defaultOpen: true,
})

const open = ref(props.defaultOpen)
const rootEl = ref<InstanceType<typeof CollapsibleRoot> | null>(null)

watch(open, (isOpen) => {
    if (isOpen) {
        // Scroll into view after the open animation completes
        setTimeout(() => {
            (rootEl.value?.$el ?? rootEl.value)?.scrollIntoView?.({
                behavior: 'smooth',
                block: 'nearest',
            })
        }, 220)
    }
})
</script>

<template>
  <CollapsibleRoot ref="rootEl" v-model:open="open" class="collapsible-section">
    <CollapsibleTrigger class="collapsible-trigger group flex w-full items-center gap-2 py-1.5 cursor-pointer select-none">
      <ChevronRight class="h-4 w-4 text-muted-foreground transition-transform duration-200" :class="{ 'rotate-90': open }" />
      <span>
        <span class="cm-serif text-sm font-semibold tracking-tight">{{ title }}</span>
        <span v-if="subtitle" class="ml-1.5 text-xs font-normal text-muted-foreground/70">&mdash; {{ subtitle }}</span>
      </span>
    </CollapsibleTrigger>
    <CollapsibleContent class="collapsible-content">
      <div class="pb-1">
        <slot />
      </div>
    </CollapsibleContent>
  </CollapsibleRoot>
</template>

<style scoped>
.collapsible-content {
    overflow: hidden;
}
.collapsible-content[data-state="open"] {
    animation: collapsible-open 0.2s ease-out;
}
.collapsible-content[data-state="closed"] {
    animation: collapsible-close 0.2s ease-out;
}
@keyframes collapsible-open {
    from { height: 0; opacity: 0; }
    to { height: var(--reka-collapsible-content-height); opacity: 1; }
}
@keyframes collapsible-close {
    from { height: var(--reka-collapsible-content-height); opacity: 1; }
    to { height: 0; opacity: 0; }
}
</style>

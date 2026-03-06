<script setup lang="ts">
import { ref, onMounted } from "vue";

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
        class="sun-moon-toggle"
        :class="{ 'is-dark': isDark }"
        :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        @click="toggle"
    >
        <!-- Sun (light mode) -->
        <svg
            class="toggle-icon toggle-sun"
            :class="{ 'is-active': !isDark }"
            viewBox="0 0 200 200"
            xmlns="http://www.w3.org/2000/svg"
        >
            <g class="sun-breathe">
                <g class="sun-rays">
                    <polygon
                        points="100,8 112,58 100,48 88,58"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="100,192 112,142 100,152 88,142"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="8,100 58,88 48,100 58,112"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="192,100 142,88 152,100 142,112"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="35,35 68,60 56,56 60,68"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="165,165 132,140 144,144 140,132"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="165,35 140,68 144,56 132,60"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                    <polygon
                        points="35,165 60,132 56,144 68,140"
                        fill="#E88845" stroke="#E88845" stroke-width="2" stroke-linejoin="round"
                    />
                </g>
                <circle cx="100" cy="100" r="44" fill="#F09855" stroke="#D16A32" stroke-width="4" />
                <path
                    d="M100,100 C106,92 116,95 117,104 C118,116 106,122 94,118 C80,112 77,96 86,84"
                    fill="none" stroke="#F0B030" stroke-width="6" stroke-linecap="round"
                />
            </g>
        </svg>

        <!-- Moon (dark mode) -->
        <svg
            class="toggle-icon toggle-moon"
            :class="{ 'is-active': isDark }"
            viewBox="0 0 200 200"
            xmlns="http://www.w3.org/2000/svg"
        >
            <path
                d="M90,30 C48,42 20,85 38,135 C54,180 110,188 150,152 C118,166 72,148 62,100 C56,68 68,42 90,30 Z"
                fill="#FFF4AA" stroke="#E5C74D" stroke-width="5" stroke-linejoin="round"
            />
            <path
                d="M80,48 C58,66 50,100 60,130"
                fill="none" stroke="#E5C74D" stroke-width="3" stroke-linecap="round"
            />
            <polygon
                class="twinkle-star"
                points="155,25 158,35 168,38 158,41 155,51 152,41 142,38 152,35"
                fill="#FFF4AA" stroke="#FFF4AA" stroke-width="1"
            />
            <polygon
                class="twinkle-star twinkle-star-2"
                points="175,65 177,72 184,74 177,76 175,83 173,76 166,74 173,72"
                fill="#FFF4AA" stroke="#FFF4AA" stroke-width="1"
            />
            <polygon
                class="twinkle-star twinkle-star-3"
                points="130,55 132,60 137,62 132,64 130,69 128,64 123,62 128,60"
                fill="#FFF4AA" stroke="#FFF4AA" stroke-width="1"
            />
            <circle cx="165" cy="30" r="1.5" fill="#FFFFFF" />
            <circle cx="185" cy="50" r="1" fill="#FFFFFF" />
        </svg>
    </button>
</template>

<style scoped>
.sun-moon-toggle {
    position: relative;
    width: 2.25rem;
    height: 2.25rem;
    cursor: pointer;
    border: 0;
    padding: 0;
    border-radius: 0.5rem;
    background: transparent;
    transition: transform 200ms ease, background 200ms ease;
    flex-shrink: 0;
}

.sun-moon-toggle:hover {
    background: hsl(var(--muted));
    transform: scale(1.05);
}

.sun-moon-toggle:focus {
    outline: none;
}

.sun-moon-toggle:focus-visible {
    outline: 2px solid hsl(var(--ring));
    outline-offset: 2px;
}

.toggle-icon {
    position: absolute;
    inset: 3px;
    width: calc(100% - 6px);
    height: calc(100% - 6px);
    display: block;
    pointer-events: none;
}

/* Sun transition */
.toggle-sun {
    opacity: 0;
    transform: rotate(-180deg) scale(0.2);
    transition: opacity 600ms cubic-bezier(0.4, 0, 0.2, 1) 80ms,
                transform 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toggle-sun.is-active {
    opacity: 1;
    transform: rotate(0deg) scale(1);
    transition: opacity 250ms cubic-bezier(0.4, 0, 0.2, 1),
                transform 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Moon transition */
.toggle-moon {
    opacity: 0;
    transform: rotate(180deg) scale(0.2);
    transition: opacity 600ms cubic-bezier(0.4, 0, 0.2, 1) 80ms,
                transform 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toggle-moon.is-active {
    opacity: 1;
    transform: rotate(0deg) scale(1);
    transition: opacity 250ms cubic-bezier(0.4, 0, 0.2, 1),
                transform 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Pause animations on inactive icon */
.toggle-sun:not(.is-active) *,
.toggle-moon:not(.is-active) * {
    animation-play-state: paused !important;
}

/* Sun ray slow spin */
.sun-rays {
    transform-origin: 100px 100px;
    animation: spin-rays 120s linear infinite;
}

@keyframes spin-rays {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Sun gentle pulse */
.sun-breathe {
    transform-origin: 100px 100px;
    animation: sun-pulse 5s ease-in-out alternate infinite;
}

@keyframes sun-pulse {
    from { transform: scale(0.97); }
    to { transform: scale(1.03); }
}

/* Star twinkling */
.twinkle-star {
    transform-origin: center;
    animation: star-twinkle 2.5s steps(4, end) infinite alternate;
}

.twinkle-star-2 {
    animation-delay: -0.8s;
    animation-duration: 2s;
}

.twinkle-star-3 {
    animation-delay: -1.5s;
    animation-duration: 3s;
}

@keyframes star-twinkle {
    0% { transform: scale(0.85) rotate(0deg); opacity: 0.7; }
    33% { transform: scale(1.15) rotate(10deg); opacity: 1; }
    66% { transform: scale(0.9) rotate(-8deg); opacity: 0.8; }
    100% { transform: scale(1.1) rotate(5deg); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
    .toggle-sun,
    .toggle-moon {
        transition: opacity 200ms ease;
        transform: none !important;
    }
    .toggle-sun.is-active,
    .toggle-moon.is-active {
        transform: none !important;
    }
    .sun-rays,
    .sun-breathe,
    .twinkle-star {
        animation: none;
    }
}
</style>

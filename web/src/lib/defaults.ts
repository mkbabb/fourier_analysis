import type { ContourSettings, AnimationSettings } from "./types";

export const CONTOUR_DEFAULTS: ContourSettings = {
    strategy: "auto",
    resize: 768,
    blur_sigma: 0.5,
    n_harmonics: 200,
    n_points: 1024,
    n_classes: 3,
    min_contour_length: 40,
    min_contour_area: 0.001,
    max_contours: 16,
    smooth_contours: 0.03,
    ml_threshold: 0.5,
    ml_detail_threshold: 0.3,
};

export const ANIMATION_DEFAULTS: AnimationSettings = {
    fps: 60,
    duration: 5000,
    max_circles: 100,
    easing: "sine",
    speed: 1,
    active_bases: ["fourier-epicycles"],
};

export function defaultContourSettings(): ContourSettings {
    return { ...CONTOUR_DEFAULTS };
}

export function defaultAnimationSettings(): AnimationSettings {
    return { ...ANIMATION_DEFAULTS, active_bases: [...ANIMATION_DEFAULTS.active_bases] };
}

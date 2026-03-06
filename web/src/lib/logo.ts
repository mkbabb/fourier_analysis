/**
 * Programmatic SVG logo generator using Fourier harmonics.
 *
 * Produces a "squiggly circle" path — a circle approximated by a small number
 * of harmonics, giving it charming imperfections that nod to epicycle drawings.
 */

/** A single Fourier harmonic descriptor. */
export interface Harmonic {
    /** Harmonic number (negative = counter-rotating). */
    n: number;
    /** Amplitude of this harmonic. */
    amplitude: number;
    /** Phase offset in radians. */
    phase: number;
}

// ---------------------------------------------------------------------------
// Tunable defaults — tweak these to adjust the logo shape.
// ---------------------------------------------------------------------------

/** Default harmonic configuration for the logo. */
export const DEFAULT_HARMONICS: Harmonic[] = [
    { n: 1, amplitude: 9, phase: 0 }, // base circle
    { n: 3, amplitude: 0.8, phase: 0.5 }, // 3rd harmonic wobble
    { n: 5, amplitude: 0.4, phase: 1.2 }, // 5th harmonic detail
    { n: -2, amplitude: 0.6, phase: 2.1 }, // counter-rotating wobble
];

/** Default center x coordinate (within a 24x24 viewBox). */
export const DEFAULT_CX = 12;

/** Default center y coordinate (within a 24x24 viewBox). */
export const DEFAULT_CY = 12;

/** Default base radius. */
export const DEFAULT_BASE_RADIUS = 9;

/** Default number of sample points along the path. */
export const DEFAULT_NUM_POINTS = 64;

// ---------------------------------------------------------------------------
// Generator
// ---------------------------------------------------------------------------

/**
 * Generate an SVG path for a squiggly circle using Fourier harmonics.
 *
 * Evaluates:
 *   x(t) = cx + sum( amplitude_k * cos(2*pi*n_k*t + phase_k) )
 *   y(t) = cy + sum( amplitude_k * sin(2*pi*n_k*t + phase_k) )
 * for t in [0, 1).
 *
 * @param options - Optional overrides for harmonics, centre, radius, and resolution.
 * @returns SVG path `d` attribute string.
 */
export function generateEpicycleLogoPath(options?: {
    harmonics?: Harmonic[];
    cx?: number;
    cy?: number;
    baseRadius?: number;
    numPoints?: number;
}): string {
    const {
        harmonics = DEFAULT_HARMONICS,
        cx = DEFAULT_CX,
        cy = DEFAULT_CY,
        numPoints = DEFAULT_NUM_POINTS,
    } = options ?? {};

    // baseRadius is accepted for API completeness but the actual radius is
    // encoded in the harmonic amplitudes. If a caller supplies a custom
    // baseRadius we scale all amplitudes proportionally.
    const baseRadius = options?.baseRadius ?? DEFAULT_BASE_RADIUS;
    const scale = baseRadius / DEFAULT_BASE_RADIUS;

    const TWO_PI = 2 * Math.PI;
    const parts: string[] = [];

    for (let i = 0; i < numPoints; i++) {
        const t = i / numPoints;
        let x = cx;
        let y = cy;

        for (const h of harmonics) {
            const angle = TWO_PI * h.n * t + h.phase;
            x += h.amplitude * scale * Math.cos(angle);
            y += h.amplitude * scale * Math.sin(angle);
        }

        // Round to 2 decimal places to keep the path string compact.
        const xr = Math.round(x * 100) / 100;
        const yr = Math.round(y * 100) / 100;

        parts.push(i === 0 ? `M${xr} ${yr}` : `L${xr} ${yr}`);
    }

    parts.push("Z");
    return parts.join(" ");
}

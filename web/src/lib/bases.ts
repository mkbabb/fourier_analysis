/**
 * Client-side basis evaluation functions for real-time rendering.
 */

import type { BasisComponent, BasisDecomposition } from "./types";

/** Fourier: sum c_k * exp(2*pi*i*k*t) */
export function evaluateFourier(
    components: BasisComponent[],
    t: number,
    maxTerms?: number,
): [number, number] {
    let re = 0,
        im = 0;
    const n = maxTerms ?? components.length;
    for (let i = 0; i < n && i < components.length; i++) {
        const c = components[i];
        const angle = 2 * Math.PI * c.index * t;
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        // c * exp(i*angle) = (c_re + i*c_im)(cos + i*sin)
        re += c.coefficient[0] * cos - c.coefficient[1] * sin;
        im += c.coefficient[0] * sin + c.coefficient[1] * cos;
    }
    return [re, im];
}

/** Chebyshev: sum c_k * T_k(s) via Clenshaw recurrence */
export function evaluateChebyshev(
    components: BasisComponent[],
    s: number,
    maxTerms?: number,
): number {
    const n = maxTerms ?? components.length;
    // Build coefficient array indexed by degree
    let maxDeg = 0;
    for (let i = 0; i < n && i < components.length; i++) {
        if (components[i].index > maxDeg) maxDeg = components[i].index;
    }
    const coeffs = new Float64Array(maxDeg + 1);
    for (let i = 0; i < n && i < components.length; i++) {
        const c = components[i];
        if (c.index >= 0 && c.index <= maxDeg) {
            coeffs[c.index] = c.coefficient[0];
        }
    }
    // Clenshaw recurrence for Chebyshev T
    if (maxDeg === 0) return coeffs[0];
    let b1 = 0,
        b2 = 0;
    for (let k = maxDeg; k >= 1; k--) {
        const tmp = 2 * s * b1 - b2 + coeffs[k];
        b2 = b1;
        b1 = tmp;
    }
    return s * b1 - b2 + coeffs[0];
}

/** Legendre: sum c_k * P_k(s) via Clenshaw recurrence */
export function evaluateLegendre(
    components: BasisComponent[],
    s: number,
    maxTerms?: number,
): number {
    const n = maxTerms ?? components.length;
    let maxDeg = 0;
    for (let i = 0; i < n && i < components.length; i++) {
        if (components[i].index > maxDeg) maxDeg = components[i].index;
    }
    const coeffs = new Float64Array(maxDeg + 1);
    for (let i = 0; i < n && i < components.length; i++) {
        const c = components[i];
        if (c.index >= 0 && c.index <= maxDeg) {
            coeffs[c.index] = c.coefficient[0];
        }
    }
    if (maxDeg === 0) return coeffs[0];
    // Clenshaw for Legendre: P_{k+1}(s) = ((2k+1)*s*P_k(s) - k*P_{k-1}(s)) / (k+1)
    let b1 = 0,
        b2 = 0;
    for (let k = maxDeg; k >= 1; k--) {
        const tmp =
            ((2 * k + 1) * s * b1) / (k + 1) - ((k + 1) * b2) / (k + 2) + coeffs[k];
        b2 = b1;
        b1 = tmp;
    }
    return s * b1 - b2 / 2 + coeffs[0];
}

/** Generic dispatch by basis name */
export function evaluateBasis(
    decomp: BasisDecomposition,
    t: number,
    maxTerms?: number,
): [number, number] {
    if (decomp.basis === "fourier") {
        return evaluateFourier(decomp.components, t, maxTerms);
    }
    // Polynomial bases need s in [-1, 1]
    const s = decomp.domain[0] + (decomp.domain[1] - decomp.domain[0]) * t;
    const evalFn =
        decomp.basis === "chebyshev" ? evaluateChebyshev : evaluateLegendre;
    const val = evalFn(decomp.components, s, maxTerms);
    return [val, 0];
}

/** Cumulative positions for epicycle chain (Fourier only) */
export function fourierPositionsAt(
    components: BasisComponent[],
    t: number,
    maxCircles?: number,
): [number, number][] {
    const positions: [number, number][] = [[0, 0]];
    let cx = 0,
        cy = 0;
    const n = maxCircles ?? components.length;
    for (let i = 0; i < n && i < components.length; i++) {
        const c = components[i];
        const angle = 2 * Math.PI * c.index * t;
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        cx += c.coefficient[0] * cos - c.coefficient[1] * sin;
        cy += c.coefficient[0] * sin + c.coefficient[1] * cos;
        positions.push([cx, cy]);
    }
    return positions;
}

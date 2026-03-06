/**
 * Web Worker for precomputing traces.
 * Receives BasisDecomposition + evaluation params, returns Float64Array traces.
 */

import type { BasisComponent, BasisDecomposition } from "./types";

interface WorkerMessage {
    id: string;
    decomposition: BasisDecomposition;
    nEval: number;
    levels?: number[];
}

interface WorkerResult {
    id: string;
    traces: Record<number, { x: Float64Array; y: Float64Array }>;
}

// Inline evaluation to avoid import issues in worker context
function evalFourier(components: BasisComponent[], t: number): [number, number] {
    let re = 0,
        im = 0;
    for (const c of components) {
        const angle = 2 * Math.PI * c.index * t;
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        re += c.coefficient[0] * cos - c.coefficient[1] * sin;
        im += c.coefficient[0] * sin + c.coefficient[1] * cos;
    }
    return [re, im];
}

function evalChebyshev(components: BasisComponent[], s: number): number {
    let maxDeg = 0;
    for (const c of components) {
        if (c.index > maxDeg) maxDeg = c.index;
    }
    const coeffs = new Float64Array(maxDeg + 1);
    for (const c of components) {
        if (c.index >= 0 && c.index <= maxDeg) coeffs[c.index] = c.coefficient[0];
    }
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

function evalLegendre(components: BasisComponent[], s: number): number {
    let maxDeg = 0;
    for (const c of components) {
        if (c.index > maxDeg) maxDeg = c.index;
    }
    const coeffs = new Float64Array(maxDeg + 1);
    for (const c of components) {
        if (c.index >= 0 && c.index <= maxDeg) coeffs[c.index] = c.coefficient[0];
    }
    if (maxDeg === 0) return coeffs[0];
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

self.onmessage = (e: MessageEvent<WorkerMessage>) => {
    const { id, decomposition, nEval, levels } = e.data;
    const traces: Record<number, { x: Float64Array; y: Float64Array }> = {};

    const computeLevels = levels ?? [decomposition.components.length];

    for (const level of computeLevels) {
        const x = new Float64Array(nEval);
        const y = new Float64Array(nEval);
        const subset = decomposition.components.slice(0, level);

        for (let i = 0; i < nEval; i++) {
            const t = i / nEval;
            if (decomposition.basis === "fourier") {
                const [re, im] = evalFourier(subset, t);
                x[i] = re;
                y[i] = im;
            } else {
                const s = -1 + 2 * t;
                const evalFn =
                    decomposition.basis === "chebyshev" ? evalChebyshev : evalLegendre;
                x[i] = evalFn(subset, s);
                y[i] = t; // Placeholder; real use has separate x/y decompositions
            }
        }
        traces[level] = { x, y };
    }

    const transferables: ArrayBuffer[] = [];
    for (const trace of Object.values(traces)) {
        transferables.push(trace.x.buffer as ArrayBuffer, trace.y.buffer as ArrayBuffer);
    }

    self.postMessage({ id, traces } satisfies WorkerResult, { transfer: transferables });
};

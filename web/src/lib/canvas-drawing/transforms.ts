import type { CanvasSurface, ViewTransform } from "./types";

export function spectrumColor(i: number, total: number): string {
    const t = i / Math.max(total - 1, 1);
    const curved = Math.pow(t, 0.6);
    const hue = (1 - curved) * 300;
    return `hsl(${hue}, 85%, 55%)`;
}

export function getPathBounds(
    xs: number[],
    ys: number[],
    surface: CanvasSurface,
): ViewTransform {
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;
    const margin = 0.15;
    const scale = Math.min(
        surface.width / (rangeX * (1 + margin * 2)),
        surface.height / (rangeY * (1 + margin * 2)),
    );
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    const w = surface.width;
    const h = surface.height;

    return {
        cx,
        cy,
        scale,
        toScreen(x: number, y: number): [number, number] {
            return [w / 2 + (x - cx) * scale, h / 2 - (y - cy) * scale];
        },
    };
}

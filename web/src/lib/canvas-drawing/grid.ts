import type { CanvasSurface, ViewTransform } from "./types";

export function drawGrid(surface: CanvasSurface, view: ViewTransform): void {
    const { ctx, width, height } = surface;
    const { cx, cy, scale, toScreen } = view;

    // Compute grid step in data space (~40px on screen)
    const rawStep = 40 / scale;
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
    const normalized = rawStep / magnitude;
    let step: number;
    if (normalized <= 2) step = 2 * magnitude;
    else if (normalized <= 5) step = 5 * magnitude;
    else step = 10 * magnitude;

    const halfW = width / (2 * scale);
    const halfH = height / (2 * scale);
    const xMin = cx - halfW;
    const xMax = cx + halfW;
    const yMin = cy - halfH;
    const yMax = cy + halfH;

    const gridXStart = Math.floor(xMin / step) * step;
    const gridXEnd = Math.ceil(xMax / step) * step;
    const gridYStart = Math.floor(yMin / step) * step;
    const gridYEnd = Math.ceil(yMax / step) * step;

    // Minor grid lines
    ctx.strokeStyle = "rgba(150, 150, 150, 0.06)";
    ctx.lineWidth = 1;
    for (let x = gridXStart; x <= gridXEnd; x += step) {
        const [sx] = toScreen(x, 0);
        ctx.beginPath();
        ctx.moveTo(sx, 0);
        ctx.lineTo(sx, height);
        ctx.stroke();
    }
    for (let y = gridYStart; y <= gridYEnd; y += step) {
        const [, sy] = toScreen(0, y);
        ctx.beginPath();
        ctx.moveTo(0, sy);
        ctx.lineTo(width, sy);
        ctx.stroke();
    }

    // Axes (if visible)
    ctx.strokeStyle = "rgba(150, 150, 150, 0.15)";
    ctx.lineWidth = 1.5;
    const [axisX] = toScreen(0, 0);
    const [, axisY] = toScreen(0, 0);
    if (axisX > 0 && axisX < width) {
        ctx.beginPath();
        ctx.moveTo(axisX, 0);
        ctx.lineTo(axisX, height);
        ctx.stroke();
    }
    if (axisY > 0 && axisY < height) {
        ctx.beginPath();
        ctx.moveTo(0, axisY);
        ctx.lineTo(width, axisY);
        ctx.stroke();
    }
}

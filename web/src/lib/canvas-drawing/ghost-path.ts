import type { CanvasSurface, ViewTransform } from "./types";

/**
 * Draw the original contour path as a faint ghost overlay.
 * @param closePath  Whether to close the path (epicycle mode closes it).
 */
export function drawGhostPath(
    surface: CanvasSurface,
    view: ViewTransform,
    pathX: number[],
    pathY: number[],
    closePath = false,
): void {
    const { ctx } = surface;
    const { toScreen } = view;

    ctx.beginPath();
    ctx.strokeStyle = closePath ? "rgba(150, 150, 150, 0.25)" : "rgba(150, 150, 150, 0.2)";
    ctx.lineWidth = closePath ? 2.5 : 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    for (let i = 0; i < pathX.length; i++) {
        const [sx, sy] = toScreen(pathX[i], pathY[i]);
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
    }
    if (closePath) ctx.closePath();
    ctx.stroke();
}

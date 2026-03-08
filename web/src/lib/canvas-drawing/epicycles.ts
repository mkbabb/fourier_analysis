import type { BasisComponent } from "@/lib/types";
import type { CanvasSurface, ViewTransform } from "./types";
import { spectrumColor } from "./transforms";

const BASE_EPICYCLE_SCALE = 0.42;
const HOVER_EPICYCLE_SCALE = 0.6;
const EPICYCLE_DISPLAY_SCALE = 0.85;

export { BASE_EPICYCLE_SCALE, HOVER_EPICYCLE_SCALE, EPICYCLE_DISPLAY_SCALE };

export interface EpicycleRegion {
    centerX: number;
    centerY: number;
    regionScale: number;
}

export function getEpicycleRegion(
    width: number,
    height: number,
    currentScale: number,
): EpicycleRegion {
    const isDesktop = width >= 768;

    if (!isDesktop) {
        const mobileS = 0.3;
        return {
            centerX: width * mobileS / 2,
            centerY: height - height * mobileS / 2,
            regionScale: mobileS,
        };
    }

    const pad = 8;
    const baseW = width * BASE_EPICYCLE_SCALE;
    const baseH = height * BASE_EPICYCLE_SCALE;
    const pivotX = pad + baseW * 0.4;
    const pivotY = height - pad - baseH * 0.4;

    return {
        centerX: pivotX,
        centerY: pivotY,
        regionScale: currentScale,
    };
}

export function isMouseInEpicycleRegion(
    mouseX: number,
    mouseY: number,
    width: number,
    height: number,
): boolean {
    if (mouseX < 0 || mouseY < 0) return false;
    const pad = 12;
    const regionW = width * HOVER_EPICYCLE_SCALE;
    const regionH = height * HOVER_EPICYCLE_SCALE;
    return mouseX < pad + regionW && mouseY > height - pad - regionH;
}

/**
 * Draw epicycle circles, arms, center dots, and endpoint dots.
 * Handles the save/translate/scale transform for desktop layout.
 */
export function drawEpicycleCircles(
    surface: CanvasSurface,
    view: ViewTransform,
    visPositions: [number, number][],
    components: BasisComponent[],
    nVis: number,
    region: EpicycleRegion,
    epicycleAlpha: number,
    lineWidths: { circle: number; arm: number },
): void {
    const { ctx, width, height } = surface;
    const { toScreen, scale } = view;
    const isDesktop = width >= 768;
    const epicycleFitScale = region.regionScale * EPICYCLE_DISPLAY_SCALE;

    ctx.save();
    if (isDesktop) {
        ctx.translate(region.centerX, region.centerY);
        ctx.scale(epicycleFitScale, epicycleFitScale);
        ctx.translate(-width / 2, -height / 2);
    }

    for (let i = 0; i < nVis; i++) {
        const [ccx, ccy] = toScreen(visPositions[i][0], visPositions[i][1]);
        const [tx, ty] = toScreen(visPositions[i + 1][0], visPositions[i + 1][1]);
        const r = components[i].amplitude * scale;
        const color = spectrumColor(i, nVis);

        // Circle
        ctx.beginPath();
        ctx.arc(ccx, ccy, r, 0, Math.PI * 2);
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.5 * epicycleAlpha;
        ctx.lineWidth = lineWidths.circle;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Arm
        ctx.beginPath();
        ctx.moveTo(ccx, ccy);
        ctx.lineTo(tx, ty);
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.75 * epicycleAlpha;
        ctx.lineWidth = lineWidths.arm;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Center dot
        ctx.beginPath();
        ctx.arc(ccx, ccy, Math.max(r * 0.1, 5.5), 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.75 * epicycleAlpha;
        ctx.fill();
        ctx.globalAlpha = 1;

        // Endpoint dot
        ctx.beginPath();
        ctx.arc(tx, ty, Math.max(r * 0.08, 4.5), 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.6 * epicycleAlpha;
        ctx.fill();
        ctx.globalAlpha = 1;
    }

    ctx.restore();
}

/** Draw the dashed connecting line from the epicycle tip to the trace position on the main canvas. */
export function drawConnectingLine(
    surface: CanvasSurface,
    view: ViewTransform,
    visPositions: [number, number][],
    tipX: number,
    tipY: number,
    region: EpicycleRegion,
    epicycleAlpha: number,
): void {
    const { ctx, width, height } = surface;
    const { toScreen } = view;
    const isDesktop = width >= 768;
    if (!isDesktop) return;

    const epicycleFitScale = region.regionScale * EPICYCLE_DISPLAY_SCALE;
    const visTip = visPositions[visPositions.length - 1];
    const [rawX, rawY] = toScreen(visTip[0], visTip[1]);
    const tipSx = region.centerX + (rawX - width / 2) * epicycleFitScale;
    const tipSy = region.centerY + (rawY - height / 2) * epicycleFitScale;
    const [traceSx, traceSy] = toScreen(tipX, tipY);

    ctx.beginPath();
    ctx.moveTo(tipSx, tipSy);
    ctx.lineTo(traceSx, traceSy);
    ctx.strokeStyle = "rgba(255, 52, 18, 0.25)";
    ctx.globalAlpha = epicycleAlpha;
    ctx.lineWidth = 1.5;
    ctx.lineCap = "round";
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
}

/** Draw the tip dot and glow at the trace position. */
export function drawTipDot(
    surface: CanvasSurface,
    view: ViewTransform,
    tipX: number,
    tipY: number,
    color: string,
): void {
    const { ctx } = surface;
    const { toScreen } = view;
    const [sx, sy] = toScreen(tipX, tipY);

    ctx.beginPath();
    ctx.arc(sx, sy, 7, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    // Glow
    ctx.beginPath();
    ctx.arc(sx, sy, 15, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 52, 18, 0.15)";
    ctx.fill();
}

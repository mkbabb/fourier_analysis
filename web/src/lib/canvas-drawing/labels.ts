import type { CanvasSurface } from "./types";
import { basisDisplay } from "@/lib/basis-display";

export function drawBasisLabels(
    surface: CanvasSurface,
    activeBases: string[],
    level: number,
): void {
    const { ctx, width } = surface;

    ctx.font = "bold 13px 'Fira Code', monospace";
    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    let yOff = 16;
    for (const basisKey of activeBases) {
        const basisName = basisKey.startsWith("fourier") ? "fourier" : basisKey;
        const cfg = basisDisplay[basisName];
        if (!cfg) continue;
        const modeLabel = basisKey === "fourier-epicycles" ? "Epicycles"
            : basisKey === "fourier-series" ? "Series"
            : cfg.label;
        ctx.fillStyle = cfg.color;
        ctx.globalAlpha = 0.9;
        ctx.fillText(`${cfg.icon} ${modeLabel}`, width - 16, yOff);
        yOff += 20;
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(150, 150, 150, 0.7)";
    ctx.fillText(`N = ${level}`, width - 16, yOff);
}

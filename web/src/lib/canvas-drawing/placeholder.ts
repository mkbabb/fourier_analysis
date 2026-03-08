import type { CanvasSurface } from "./types";

export function drawPlaceholder(surface: CanvasSurface, hasImage: boolean): void {
    const { ctx, width, height } = surface;
    ctx.clearRect(0, 0, width, height);

    // Subtle grid
    ctx.strokeStyle = "rgba(150, 150, 150, 0.07)";
    ctx.lineWidth = 1;
    const step = 40;
    for (let x = step; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    for (let y = step; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Dashed rounded rect in center
    const boxW = Math.min(280, width * 0.6);
    const boxH = 100;
    const bx = (width - boxW) / 2;
    const by = (height - boxH) / 2;
    const r = 12;
    ctx.beginPath();
    ctx.roundRect(bx, by, boxW, boxH, r);
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = "rgba(150, 150, 150, 0.25)";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.setLineDash([]);

    // Upload arrow icon
    const cx = width / 2;
    const cy = height / 2 - 12;
    ctx.strokeStyle = "rgba(150, 150, 150, 0.4)";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(cx, cy - 10);
    ctx.lineTo(cx, cy + 10);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - 7, cy - 3);
    ctx.lineTo(cx, cy - 10);
    ctx.lineTo(cx + 7, cy - 3);
    ctx.stroke();

    // Text
    ctx.fillStyle = "rgba(150, 150, 150, 0.6)";
    ctx.font = "500 13px 'Fira Code', monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const msg = hasImage ? "Computing..." : "Drag & drop an image here";
    ctx.fillText(msg, cx, height / 2 + 18);
}

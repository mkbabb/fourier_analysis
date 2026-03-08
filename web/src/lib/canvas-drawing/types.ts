export interface CanvasSurface {
    ctx: CanvasRenderingContext2D;
    width: number;
    height: number;
    dpr: number;
}

export interface ViewTransform {
    cx: number;
    cy: number;
    scale: number;
    toScreen(x: number, y: number): [number, number];
}

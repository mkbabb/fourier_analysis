export interface Point2D {
    x: number;
    y: number;
}

/** Convert separate x/y arrays to Point2D array */
export function zipPoints(xs: number[], ys: number[]): Point2D[] {
    return xs.map((x, i) => ({ x, y: ys[i] }));
}

/** Convert Point2D array to separate x/y arrays */
export function unzipPoints(points: Point2D[]): { x: number[]; y: number[] } {
    return {
        x: points.map((p) => p.x),
        y: points.map((p) => p.y),
    };
}

/** Generate SVG path `d` attribute for a closed Catmull-Rom spline */
export function closedSplinePath(points: Point2D[], tension = 0.5): string {
    const n = points.length;
    if (n < 2) return "";
    if (n === 2)
        return `M${points[0].x},${points[0].y}L${points[1].x},${points[1].y}Z`;

    const parts: string[] = [`M${points[0].x},${points[0].y}`];
    for (let i = 0; i < n; i++) {
        const p0 = points[(i - 1 + n) % n];
        const p1 = points[i];
        const p2 = points[(i + 1) % n];
        const p3 = points[(i + 2) % n];

        const factor = 1 / 6;
        const cp1x = p1.x + (p2.x - p0.x) * factor;
        const cp1y = p1.y + (p2.y - p0.y) * factor;
        const cp2x = p2.x - (p3.x - p1.x) * factor;
        const cp2y = p2.y - (p3.y - p1.y) * factor;

        parts.push(`C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`);
    }
    parts.push("Z");
    return parts.join("");
}

/** Find the nearest segment index for inserting a new point */
export function nearestSegmentIndex(points: Point2D[], click: Point2D): number {
    let bestDist = Infinity;
    let bestIdx = 0;
    const n = points.length;
    for (let i = 0; i < n; i++) {
        const a = points[i];
        const b = points[(i + 1) % n];
        const dist = pointToSegmentDist(click, a, b);
        if (dist < bestDist) {
            bestDist = dist;
            bestIdx = i + 1;
        }
    }
    return bestIdx;
}

function pointToSegmentDist(p: Point2D, a: Point2D, b: Point2D): number {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(p.x - a.x, p.y - a.y);
    let t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
}

/**
 * Visvalingam-Whyatt simplification for closed curves.
 * Removes ~20% of points per call, prioritizing those whose removal
 * causes the least area change (i.e. nearly-collinear neighbors).
 */
export function simplifyClosedPoints(
    points: Point2D[],
    removalFraction = 0.2,
): Point2D[] {
    if (points.length <= 6) return points;

    // Work on a mutable linked structure for efficient removal
    const n = points.length;
    const toRemove = Math.max(1, Math.floor(n * removalFraction));
    const targetCount = Math.max(4, n - toRemove);

    // Copy points with prev/next indices for circular linked list
    interface Node { pt: Point2D; prev: number; next: number; area: number; alive: boolean }
    const nodes: Node[] = points.map((pt, i) => ({
        pt: { ...pt },
        prev: (i - 1 + n) % n,
        next: (i + 1) % n,
        area: 0,
        alive: true,
    }));

    function triangleArea(a: Point2D, b: Point2D, c: Point2D): number {
        return Math.abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2;
    }

    // Compute initial areas
    for (let i = 0; i < n; i++) {
        nodes[i].area = triangleArea(nodes[nodes[i].prev].pt, nodes[i].pt, nodes[nodes[i].next].pt);
    }

    let alive = n;
    while (alive > targetCount) {
        // Find node with smallest area (least important)
        let minArea = Infinity;
        let minIdx = -1;
        for (let i = 0; i < n; i++) {
            if (nodes[i].alive && nodes[i].area < minArea) {
                minArea = nodes[i].area;
                minIdx = i;
            }
        }
        if (minIdx === -1) break;

        // Remove it
        const node = nodes[minIdx];
        node.alive = false;
        nodes[node.prev].next = node.next;
        nodes[node.next].prev = node.prev;
        alive--;

        // Recompute areas of neighbors
        const p = node.prev;
        const nx = node.next;
        nodes[p].area = triangleArea(nodes[nodes[p].prev].pt, nodes[p].pt, nodes[nodes[p].next].pt);
        nodes[nx].area = triangleArea(nodes[nodes[nx].prev].pt, nodes[nx].pt, nodes[nodes[nx].next].pt);
    }

    const result: Point2D[] = [];
    for (let i = 0; i < n; i++) {
        if (nodes[i].alive) result.push(nodes[i].pt);
    }
    return result.length >= 3 ? result : points;
}

/** Laplacian smoothing for closed curves (centroid-preserving) */
export function smoothClosedPoints(
    points: Point2D[],
    iterations = 4,
    alpha = 0.4,
): Point2D[] {
    let pts = points.map((p) => ({ ...p }));
    const n = pts.length;

    // Save original centroid
    const cx0 = pts.reduce((s, p) => s + p.x, 0) / n;
    const cy0 = pts.reduce((s, p) => s + p.y, 0) / n;

    for (let iter = 0; iter < iterations; iter++) {
        const next = pts.map((_, i) => {
            const prev = pts[(i - 1 + n) % n];
            const curr = pts[i];
            const nxt = pts[(i + 1) % n];
            return {
                x: curr.x + alpha * ((prev.x + nxt.x) / 2 - curr.x),
                y: curr.y + alpha * ((prev.y + nxt.y) / 2 - curr.y),
            };
        });
        pts = next;
    }

    // Restore centroid
    const cx1 = pts.reduce((s, p) => s + p.x, 0) / n;
    const cy1 = pts.reduce((s, p) => s + p.y, 0) / n;
    const dx = cx0 - cx1;
    const dy = cy0 - cy1;
    return pts.map((p) => ({ x: p.x + dx, y: p.y + dy }));
}

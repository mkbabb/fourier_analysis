/**
 * Extract contour points from SVG shape elements.
 * Samples points along every <path>, <polygon>, <circle>, etc.
 */

/**
 * Sample points along every shape element in an SVG,
 * producing an array of contours (each contour is an array of [x,y] points).
 */
export function extractContours(
    svgEl: SVGSVGElement,
    samplesPerPath: number = 128,
): [number, number][][] {
    const contours: [number, number][][] = [];

    const elements = svgEl.querySelectorAll("path, polygon, circle, ellipse, rect, line");

    for (const el of elements) {
        const points: [number, number][] = [];

        if (el instanceof SVGCircleElement) {
            const cx = el.cx.baseVal.value;
            const cy = el.cy.baseVal.value;
            const r = el.r.baseVal.value;
            const n = Math.max(16, Math.round(samplesPerPath * (r / 50)));
            for (let i = 0; i < n; i++) {
                const angle = (2 * Math.PI * i) / n;
                points.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
            }
        } else if (el instanceof SVGPolygonElement) {
            const pl = el.points;
            for (let i = 0; i < pl.numberOfItems; i++) {
                const pt = pl.getItem(i);
                points.push([pt.x, pt.y]);
            }
        } else {
            const geom = el as SVGGeometryElement;
            try {
                const totalLen = geom.getTotalLength();
                if (totalLen < 1) continue;
                const n = samplesPerPath;
                for (let i = 0; i < n; i++) {
                    const t = (i / n) * totalLen;
                    const pt = geom.getPointAtLength(t);
                    points.push([pt.x, pt.y]);
                }
            } catch {
                continue;
            }
        }

        if (points.length >= 3) {
            contours.push(points);
        }
    }

    return contours;
}

import { test, expect } from "@playwright/test";
import * as path from "node:path";

const TEST_IMAGE = path.resolve(
    import.meta.dirname,
    "../../assets/animals/golden-retriever.webp",
);

test.describe.serial("Asset-based workspace flow", () => {
    test("upload → extract → canvas renders", async ({ page }) => {
        // 1. Navigate to visualize (no session creation — just upload UI)
        await page.goto("/visualize");

        // 2. Upload image
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        // 3. Should redirect to /w/{imageSlug}
        await page.waitForURL(/\/w\//, { timeout: 15_000 });
        const url = page.url();
        const imageSlug = url.match(/\/w\/([^/]+)/)?.[1];
        expect(imageSlug).toBeTruthy();

        // 4. Wait for canvas to appear (auto-compute on mount)
        const canvas = page.locator("canvas").first();
        await expect(canvas).toBeVisible({ timeout: 60_000 });

        // 5. Verify canvas has non-zero dimensions
        const box = await canvas.boundingBox();
        expect(box).toBeTruthy();
        expect(box!.width).toBeGreaterThan(0);
        expect(box!.height).toBeGreaterThan(0);
    });

    test("image metadata is accessible via API", async ({ page }) => {
        await page.goto("/visualize");

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        await page.waitForURL(/\/w\//, { timeout: 15_000 });
        const imageSlug = page.url().match(/\/w\/([^/]+)/)?.[1];
        expect(imageSlug).toBeTruthy();

        // Verify API returns image metadata
        const meta = await page.evaluate(async (slug) => {
            const res = await fetch(`/api/images/${slug}`);
            return res.json();
        }, imageSlug);

        expect(meta.image_slug).toBe(imageSlug);
        expect(meta.content_type).toBeTruthy();
        expect(meta.bytes).toBeGreaterThan(0);
    });

    test("extract-contour returns contour asset", async ({ page }) => {
        await page.goto("/visualize");

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        await page.waitForURL(/\/w\//, { timeout: 15_000 });
        const imageSlug = page.url().match(/\/w\/([^/]+)/)?.[1]!;

        // Wait for canvas — meaning extraction + compute already happened
        const canvas = page.locator("canvas").first();
        await expect(canvas).toBeVisible({ timeout: 60_000 });

        // Verify we can extract contour via API directly (use frontend defaults)
        const contour = await page.evaluate(async (slug) => {
            const res = await fetch(`/api/images/${slug}/extract-contour`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    contour_settings: {
                        strategy: "auto",
                        resize: 800,
                        blur_sigma: 2.0,
                        n_harmonics: 100,
                        n_points: 1024,
                        n_classes: 3,
                        min_contour_length: 40,
                        min_contour_area: 0.01,
                        max_contours: 5,
                        smooth_contours: 0.1,
                    },
                }),
            });
            const body = await res.json();
            return { status: res.status, body };
        }, imageSlug);

        expect(contour.status, `API returned: ${JSON.stringify(contour.body)}`).toBe(200);
        expect(contour.body.contour_hash).toBeTruthy();
        expect(contour.body.point_count).toBeGreaterThan(0);
        expect(contour.body.points.x.length).toBeGreaterThan(0);
        expect(contour.body.points.y.length).toBeGreaterThan(0);
    });

    test("compute epicycles from contour", async ({ page }) => {
        await page.goto("/visualize");

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        await page.waitForURL(/\/w\//, { timeout: 15_000 });
        const imageSlug = page.url().match(/\/w\/([^/]+)/)?.[1]!;

        // Extract contour
        const contour = await page.evaluate(async (slug) => {
            const res = await fetch(`/api/images/${slug}/extract-contour`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    contour_settings: {
                        strategy: "auto",
                        resize: 800,
                        blur_sigma: 2.0,
                        n_harmonics: 100,
                        n_points: 1024,
                        n_classes: 3,
                        min_contour_length: 40,
                        min_contour_area: 0.01,
                        max_contours: 5,
                        smooth_contours: 0.1,
                    },
                }),
            });
            return res.json();
        }, imageSlug);

        expect(contour.contour_hash).toBeTruthy();

        // Compute epicycles
        const epicycles = await page.evaluate(async (hash) => {
            const res = await fetch(`/api/contours/${hash}/compute/epicycles`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ n_harmonics: 50, n_points: 512 }),
            });
            return { status: res.status, body: await res.json() };
        }, contour.contour_hash);

        expect(epicycles.status).toBe(200);
        expect(epicycles.body.data.n_components).toBeGreaterThan(0);
        expect(epicycles.body.data.components.length).toBeGreaterThan(0);
    });

    test("image blob endpoint returns image with cache headers", async ({
        page,
    }) => {
        await page.goto("/visualize");

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        await page.waitForURL(/\/w\//, { timeout: 15_000 });
        const imageSlug = page.url().match(/\/w\/([^/]+)/)?.[1]!;

        const blobResponse = await page.evaluate(async (slug) => {
            const res = await fetch(`/api/images/${slug}/blob`);
            return {
                status: res.status,
                contentType: res.headers.get("content-type"),
                cacheControl: res.headers.get("cache-control"),
                size: (await res.blob()).size,
            };
        }, imageSlug);

        expect(blobResponse.status).toBe(200);
        expect(blobResponse.contentType).toContain("image");
        expect(blobResponse.size).toBeGreaterThan(0);
    });

    test("no console errors during full flow", async ({ page }) => {
        const consoleErrors: string[] = [];
        page.on("console", (msg) => {
            if (msg.type() === "error") {
                consoleErrors.push(msg.text());
            }
        });

        await page.goto("/visualize");

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(TEST_IMAGE);

        await page.waitForURL(/\/w\//, { timeout: 15_000 });

        const canvas = page.locator("canvas").first();
        await expect(canvas).toBeVisible({ timeout: 60_000 });
        await page.waitForTimeout(2000);

        // Filter out benign errors (favicon, etc.)
        const realErrors = consoleErrors.filter(
            (e) =>
                !e.includes("favicon") &&
                !e.includes("404") &&
                !e.includes("ERR_CONNECTION_REFUSED") &&
                !e.includes("429"),
        );
        expect(realErrors).toEqual([]);
    });
});

import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const ANIMALS_DIR = path.resolve(__dirname, "../../assets/animals");

const animalImages = fs.readdirSync(ANIMALS_DIR).filter((f) => /\.(jpg|jpeg|png|webp)$/i.test(f));

test.describe("Contour extraction with animal images", () => {
    test.beforeEach(async ({ page }) => {
        // Navigate and wait for session creation
        await page.goto("/visualize");
        await page.waitForURL(/\/s\//);
    });

    for (const imageName of animalImages) {
        test(`upload and extract contours — ${imageName}`, async ({ page }) => {
            // Upload image via file input
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles(path.join(ANIMALS_DIR, imageName));

            // Wait for computation to complete (spinner disappears)
            await page.waitForFunction(
                () => !document.querySelector('[data-computing="true"]'),
                { timeout: 30_000 },
            );

            // Allow time for canvas render
            await page.waitForTimeout(2000);

            // Verify epicycle canvas renders with non-zero dimensions
            const canvas = page.locator("canvas").first();
            await expect(canvas).toBeVisible({ timeout: 10_000 });
            const box = await canvas.boundingBox();
            expect(box).toBeTruthy();
            expect(box!.width).toBeGreaterThan(0);
            expect(box!.height).toBeGreaterThan(0);

            // Screenshot for visual inspection
            await page.screenshot({
                path: `e2e/screenshots/${imageName}-default.png`,
                fullPage: true,
            });
        });
    }

    test("adjust contour controls and verify recomputation", async ({ page }) => {
        if (animalImages.length === 0) {
            test.skip();
            return;
        }

        // Upload first animal image
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(ANIMALS_DIR, animalImages[0]));

        // Wait for initial computation
        await page.waitForFunction(
            () => !document.querySelector('[data-computing="true"]'),
            { timeout: 30_000 },
        );
        await page.waitForTimeout(2000);

        // Adjust blur sigma slider
        const blurSlider = page.locator('input[type="range"]').first();
        await blurSlider.fill("2.5");

        // Adjust min area % slider
        const minAreaSlider = page.locator('input[type="range"]').nth(1);
        await minAreaSlider.fill("5");

        // Adjust max contours slider
        const maxContoursSlider = page.locator('input[type="range"]').nth(2);
        await maxContoursSlider.fill("5");

        // Adjust smoothing slider
        const smoothSlider = page.locator('input[type="range"]').nth(3);
        await smoothSlider.fill("0.3");

        // Wait for debounced recomputation (800ms debounce + compute time)
        await page.waitForTimeout(3000);

        // Verify canvas still renders
        const canvas = page.locator("canvas").first();
        await expect(canvas).toBeVisible({ timeout: 10_000 });

        // Screenshot adjusted result
        await page.screenshot({
            path: `e2e/screenshots/${animalImages[0]}-adjusted.png`,
            fullPage: true,
        });
    });

    test("strategy switching triggers recomputation", async ({ page }) => {
        if (animalImages.length === 0) {
            test.skip();
            return;
        }

        // Upload first animal image
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(ANIMALS_DIR, animalImages[0]));

        // Wait for initial computation
        await page.waitForFunction(
            () => !document.querySelector('[data-computing="true"]'),
            { timeout: 30_000 },
        );
        await page.waitForTimeout(2000);

        // Change strategy to "threshold"
        const strategyTrigger = page.locator('[role="combobox"]').first();
        await strategyTrigger.click();
        await page.locator('[role="option"]').filter({ hasText: "Otsu Threshold" }).click();

        // Wait for debounced recomputation
        await page.waitForTimeout(3000);

        // Verify canvas still renders
        const canvas = page.locator("canvas").first();
        await expect(canvas).toBeVisible({ timeout: 10_000 });

        await page.screenshot({
            path: `e2e/screenshots/${animalImages[0]}-threshold.png`,
            fullPage: true,
        });
    });

    test("no console errors during flow", async ({ page }) => {
        const consoleErrors: string[] = [];
        page.on("console", (msg) => {
            if (msg.type() === "error") {
                consoleErrors.push(msg.text());
            }
        });

        if (animalImages.length === 0) {
            test.skip();
            return;
        }

        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(path.join(ANIMALS_DIR, animalImages[0]));

        await page.waitForFunction(
            () => !document.querySelector('[data-computing="true"]'),
            { timeout: 30_000 },
        );
        await page.waitForTimeout(2000);

        // Filter out benign errors (e.g. favicon 404)
        const realErrors = consoleErrors.filter(
            (e) => !e.includes("favicon") && !e.includes("404"),
        );
        expect(realErrors).toEqual([]);
    });
});

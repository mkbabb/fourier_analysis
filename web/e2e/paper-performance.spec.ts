import { test, expect, type Page } from "@playwright/test";

const MAX_MOUNTED_SECTIONS = 18;
const DESKTOP_SCROLL_OFFSET_PX = 16;

async function stubRemoteAssets(page: Page) {
    await page.route(/https:\/\/(fonts\.googleapis\.com|fonts\.gstatic\.com|cdn\.jsdelivr\.net)\/.*/, async (route) => {
        const type = route.request().resourceType();
        if (type === "stylesheet") {
            await route.fulfill({
                status: 200,
                contentType: "text/css",
                body: "",
            });
            return;
        }

        if (type === "font") {
            await route.fulfill({
                status: 204,
                body: "",
            });
            return;
        }

        await route.abort();
    });
}

function parseOverlayPage(text: string): number {
    const match = text.match(/pg\s*(\d+)\s*\/\s*(\d+)/i);
    if (!match) {
        throw new Error(`Unexpected overlay text: ${text}`);
    }
    return Number(match[1]);
}

async function waitForPaperReady(page: Page) {
    await page.goto("/paper", { waitUntil: "domcontentloaded" });
    await expect(page.locator(".paper-section").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.locator(".overlay-page")).toHaveText(/pg\s*4\s*\/\s*97/i, {
        timeout: 15_000,
    });
}

async function mountedSectionCount(page: Page): Promise<number> {
    return page.locator(".paper-section").count();
}

async function overlayText(page: Page): Promise<string> {
    return page.locator(".overlay-page").innerText();
}

async function scrollPaperTo(page: Page, top: number) {
    await page.locator(".paper-scroll").evaluate((element, nextTop) => {
        (element as HTMLElement).scrollTo({ top: nextTop as number, behavior: "instant" });
    }, top);
    await page.waitForTimeout(160);
}

async function getScrollMetrics(page: Page): Promise<{ maxScrollTop: number }> {
    return page.locator(".paper-scroll").evaluate((element) => {
        const scroller = element as HTMLElement;
        return {
            maxScrollTop: Math.max(0, scroller.scrollHeight - scroller.clientHeight),
        };
    });
}

async function getSectionViewportTop(page: Page, id: string): Promise<number> {
    return page.evaluate((targetId) => {
        const scroller = document.querySelector(".paper-scroll");
        const target = document.getElementById(targetId);
        if (!(scroller instanceof HTMLElement) || !(target instanceof HTMLElement)) {
            throw new Error(`Missing section or scroller for ${targetId}`);
        }
        return target.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
    }, id);
}

async function overlayOpacity(page: Page): Promise<number> {
    return page.locator(".teleport-overlay").evaluate((element) =>
        Number.parseFloat(getComputedStyle(element as HTMLElement).opacity),
    );
}

test.describe("Paper performance", () => {
    test.describe.configure({ mode: "serial" });

    test.beforeEach(async ({ page }) => {
        await stubRemoteAssets(page);
    });

    test("initial paper render stays windowed", async ({ page }) => {
        await waitForPaperReady(page);

        await expect(page.locator(".overlay-page")).toHaveText(/pg\s*4\s*\/\s*97/i);
        expect(await mountedSectionCount(page)).toBeLessThanOrEqual(MAX_MOUNTED_SECTIONS);
    });

    test("forward scrolling never regresses the page indicator back to 1", async ({ page }) => {
        await waitForPaperReady(page);

        const { maxScrollTop } = await getScrollMetrics(page);
        const checkpoints = Array.from({ length: 10 }, (_, index) =>
            Math.round((maxScrollTop * (index + 1)) / 11),
        ).filter((top) => top > 2000);

        const sampledPages: number[] = [];
        for (const top of checkpoints) {
            await scrollPaperTo(page, top);
            sampledPages.push(parseOverlayPage(await overlayText(page)));
        }

        expect(sampledPages.length).toBeGreaterThan(0);
        expect(sampledPages.every((sample) => sample > 1)).toBe(true);
    });

    test("far TOC jumps land on DFT as Matrix Multiplication without over-mounting", async ({ page }) => {
        await waitForPaperReady(page);

        await page.locator('[data-toc-id="the-discrete-fourier-transform"]').click();
        await expect(page.locator('[data-toc-id="dft-as-matrix-multiplication"]')).toBeVisible();
        await page.locator('[data-toc-id="dft-as-matrix-multiplication"]').click();
        await expect.poll(() => overlayOpacity(page), { timeout: 1_000 }).toBeGreaterThan(0.05);

        await expect
            .poll(async () => {
                const [overlay, top] = await Promise.all([
                    overlayText(page),
                    getSectionViewportTop(page, "dft-as-matrix-multiplication"),
                ]);
                return {
                    page: parseOverlayPage(overlay),
                    aligned: Math.abs(top - DESKTOP_SCROLL_OFFSET_PX) <= 32,
                };
            }, {
                timeout: 10_000,
            })
            .toEqual({
                page: 59,
                aligned: true,
            });

        const top = await getSectionViewportTop(page, "dft-as-matrix-multiplication");
        expect(Math.abs(top - DESKTOP_SCROLL_OFFSET_PX)).toBeLessThanOrEqual(32);
        expect(parseOverlayPage(await overlayText(page))).toBe(59);
        expect(await mountedSectionCount(page)).toBeLessThanOrEqual(MAX_MOUNTED_SECTIONS);
    });

    test("long scroll keeps mounted sections bounded and logs no browser errors", async ({ page }) => {
        const consoleErrors: string[] = [];
        const pageErrors: string[] = [];

        page.on("console", (message) => {
            if (message.type() === "error") {
                consoleErrors.push(message.text());
            }
        });
        page.on("pageerror", (error) => {
            pageErrors.push(error.message);
        });

        await waitForPaperReady(page);

        const { maxScrollTop } = await getScrollMetrics(page);
        const checkpoints = Array.from({ length: 12 }, (_, index) =>
            Math.round((maxScrollTop * index) / 11),
        );
        const mountedCounts: number[] = [];

        for (const top of checkpoints) {
            await scrollPaperTo(page, top);
            mountedCounts.push(await mountedSectionCount(page));
        }

        expect(Math.max(...mountedCounts)).toBeLessThanOrEqual(MAX_MOUNTED_SECTIONS);
        expect(pageErrors).toEqual([]);
        expect(
            consoleErrors.filter(
                (message) => !message.includes("favicon") && !message.includes("404"),
            ),
        ).toEqual([]);
    });
});

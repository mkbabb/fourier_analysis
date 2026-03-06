import katex from "katex";

// Module-level cache: persists across all component instances for the
// lifetime of the page, avoiding redundant katex.renderToString calls.
const cache = new Map<string, string>();

export function useKatex() {
    function renderInline(tex: string): string {
        const key = `i:${tex}`;
        let html = cache.get(key);
        if (html === undefined) {
            html = katex.renderToString(tex, {
                throwOnError: false,
                displayMode: false,
            });
            cache.set(key, html);
        }
        return html;
    }

    function renderDisplay(tex: string): string {
        const key = `d:${tex}`;
        let html = cache.get(key);
        if (html === undefined) {
            html = katex.renderToString(tex, {
                throwOnError: false,
                displayMode: true,
            });
            cache.set(key, html);
        }
        return html;
    }

    return { renderInline, renderDisplay };
}

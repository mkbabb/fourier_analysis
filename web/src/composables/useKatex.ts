import katex from "katex";

// Custom macros matching fourier_paper.tex preamble
const macros: Record<string, string> = {
    "\\deriv": "\\mathrm{d}",
    "\\ihat": "\\boldsymbol{\\hat{\\imath}}",
    "\\jhat": "\\boldsymbol{\\hat{\\jmath}}",
    "\\khat": "\\boldsymbol{\\hat{k}}",
    "\\ehat": "\\boldsymbol{\\hat{e}}",
    "\\dott": "\\boldsymbol{\\cdot}",
    "\\leftrightarrow": "\\longleftrightarrow",
    "\\Leftrightarrow": "\\Longleftrightarrow",
};

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
                macros,
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
                macros,
            });
            cache.set(key, html);
        }
        return html;
    }

    return { renderInline, renderDisplay };
}

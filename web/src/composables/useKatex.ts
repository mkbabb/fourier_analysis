import katex from "katex";

export function useKatex() {
    function renderInline(tex: string): string {
        return katex.renderToString(tex, {
            throwOnError: false,
            displayMode: false,
        });
    }

    function renderDisplay(tex: string): string {
        return katex.renderToString(tex, {
            throwOnError: false,
            displayMode: true,
        });
    }

    return { renderInline, renderDisplay };
}

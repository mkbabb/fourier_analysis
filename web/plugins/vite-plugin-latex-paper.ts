/**
 * Vite plugin: parses fourier_paper.tex at build time and exposes
 * structured paper content as a virtual module `virtual:paper-content`.
 *
 * Any change to the .tex file triggers an HMR update.
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Plugin } from "vite";

// ── Types ────────────────────────────────────────────────────────────

export interface PaperTheoremData {
    type: "theorem" | "definition" | "lemma" | "proposition" | "corollary" | "aside" | "example";
    name?: string;
    body: string;
    math?: string[];
}

export interface PaperFigureData {
    filename: string;
    caption: string;
    label?: string;
}

export interface PaperSectionData {
    id: string;
    number: string;
    title: string;
    paragraphs: string[];
    theorems?: PaperTheoremData[];
    figures?: PaperFigureData[];
    subsections?: PaperSectionData[];
    callout?: { text: string; link: string };
}

// ── LaTeX Parser ─────────────────────────────────────────────────────

/**
 * Strip LaTeX formatting commands from prose text, preserving $...$ math
 * delimiters verbatim so KaTeX can render them later.
 */
function cleanLatex(text: string): string {
    // Split on $...$ boundaries. Odd-indexed segments are math.
    const parts = text.split(/(\$[^$]*\$)/g);
    for (let i = 0; i < parts.length; i++) {
        if (i % 2 === 1) continue; // skip math segments
        parts[i] = cleanProseSegment(parts[i]);
    }
    return parts.join("").replace(/  +/g, " ").trim();
}

/** Clean a prose (non-math) segment of LaTeX formatting. */
function cleanProseSegment(text: string): string {
    return (
        text
            // \textit{...} / \textbf{...} / \emph{...}
            .replace(/\\textit\{([^}]*)\}/g, "$1")
            .replace(/\\textbf\{([^}]*)\}/g, "$1")
            .replace(/\\emph\{([^}]*)\}/g, "$1")
            .replace(/\\text\{([^}]*)\}/g, "$1")
            // \cite{...} -> ""
            .replace(/\\cite\{[^}]*\}/g, "")
            // \ref/\eqref/\label -> ""
            .replace(/\\(?:ref|eqref|label|hyperref)\{[^}]*\}/g, "")
            // Chapter~/Section~ refs
            .replace(/(?:Chapters?|Sections?|Theorem|Figure)~\\ref\{[^}]*\}/g, "")
            .replace(/\\S\\ref\{[^}]*\}/g, "")
            // \S ref (§)
            .replace(/\\S\\/g, "§")
            // ~ -> space
            .replace(/~/g, " ")
            // \, \; \: \! -> space or nothing
            .replace(/\\[,;:!]/g, " ")
            // \quad, \qquad
            .replace(/\\q?quad/g, " ")
            // \\ -> space (line breaks in text)
            .replace(/\\\\/g, " ")
            // \newline
            .replace(/\\newline/g, " ")
            // \noindent, \paragraph{...}
            .replace(/\\noindent\s*/g, "")
            .replace(/\\paragraph\{([^}]*)\}/g, "$1.")
            // \begin{quote}...\end{quote} -> strip environment delimiters
            .replace(/\\begin\{quote\}/g, "")
            .replace(/\\end\{quote\}/g, "")
            // Remove \begin{figure}...\end{figure} blocks (figures extracted separately)
            .replace(/\\begin\{figure\}[\s\S]*?\\end\{figure\}/g, "")
            // Remove \begin{center}...\end{center} tables (too complex for web)
            .replace(/\\begin\{center\}[\s\S]*?\\end\{center\}/g, "")
            // \@ -> nothing
            .replace(/\\@/g, "")
            // Arrow symbols (prose only — KaTeX handles these in math)
            .replace(/\\implies/g, "⇒")
            .replace(/\\iff/g, "⇔")
            .replace(/\\infty/g, "∞")
            .replace(/\\ldots/g, "…")
            .replace(/\\cdots/g, "⋯")
            .replace(/\\dots/g, "…")
    );
}

/** Convert inline LaTeX math to $...$ delimited form for KaTeX rendering. */
function wrapInlineMath(text: string): string {
    // Already has $...$, leave those. Convert \( ... \) if present.
    return text.replace(/\\\(([^)]+)\\\)/g, "$$$1$$");
}

/** Extract display math from align/equation environments. */
function extractMathBlocks(content: string): string[] {
    const mathBlocks: string[] = [];
    // Match equation, align, align* environments
    const mathRe =
        /\\begin\{(equation|align|align\*)\}([\s\S]*?)\\end\{\1\}/g;
    let m: RegExpExecArray | null;
    while ((m = mathRe.exec(content)) !== null) {
        const envName = m[1]; // "equation", "align", or "align*"
        let math = m[2].trim();
        // Remove \label{...}
        math = math.replace(/\\label\{[^}]*\}/g, "").trim();
        if (math) {
            // Wrap align/align* content in \begin{aligned}...\end{aligned}
            // so KaTeX can render the & and \\ correctly
            if (envName === "align" || envName === "align*") {
                math = `\\begin{aligned} ${math} \\end{aligned}`;
            }
            mathBlocks.push(math);
        }
    }
    return mathBlocks;
}

/**
 * Extract an optional bracketed name like [Foo] or [$\mathbf{L}^2{[a,b]}$, Bar]
 * from the start of content, correctly handling nested brackets.
 */
function extractBracketedName(content: string): { name: string | null; rest: string } {
    const trimmed = content.replace(/^\s*/, "");
    if (!trimmed.startsWith("[")) return { name: null, rest: content };

    let depth = 0;
    for (let i = 0; i < trimmed.length; i++) {
        if (trimmed[i] === "[") depth++;
        else if (trimmed[i] === "]") {
            depth--;
            if (depth === 0) {
                return {
                    name: trimmed.slice(1, i),
                    rest: trimmed.slice(i + 1),
                };
            }
        }
    }
    // Unbalanced — fall back to no name
    return { name: null, rest: content };
}

/** Parse a theorem/definition/lemma/aside/example/corollary environment. */
function parseTheorem(
    envType: string,
    content: string,
): PaperTheoremData | null {
    const typeMap: Record<string, PaperTheoremData["type"]> = {
        theorem: "theorem",
        definition: "definition",
        lemma: "lemma",
        proposition: "proposition",
        corollary: "corollary",
        aside: "aside",
        example: "example",
    };
    const type = typeMap[envType];
    if (!type) return null;

    // Extract optional name from [...] — bracket-aware to handle nested [a,b]
    const { name: rawName, rest: body } = extractBracketedName(content);
    const name = rawName ? cleanLatex(rawName) : undefined;

    // Extract math blocks
    const math = extractMathBlocks(body);

    // Get the text content (everything outside math environments)
    let textBody = body
        .replace(
            /\\begin\{(equation|align|align\*)\}[\s\S]*?\\end\{\1\}/g,
            "",
        )
        .replace(/\\begin\{proof\}[\s\S]*?\\end\{proof\}/g, "")
        .trim();

    textBody = cleanLatex(textBody);
    textBody = wrapInlineMath(textBody);

    if (!textBody && math.length === 0) return null;

    return {
        type,
        ...(name && { name }),
        body: textBody,
        ...(math.length > 0 && { math }),
    };
}

/**
 * Slugify a section title to create an HTML id.
 */
function slugify(text: string): string {
    return text
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
}

/**
 * Split text into paragraphs (separated by blank lines),
 * excluding theorem/proof/math environments.
 */
function extractParagraphs(text: string): string[] {
    // Remove theorem-like environments (handled separately)
    let cleaned = text;
    const envTypes = [
        "theorem",
        "definition",
        "lemma",
        "proposition",
        "corollary",
        "aside",
        "example",
        "proof",
    ];
    for (const env of envTypes) {
        const re = new RegExp(
            `\\\\begin\\{${env}\\}[\\s\\S]*?\\\\end\\{${env}\\}`,
            "g",
        );
        cleaned = cleaned.replace(re, "");
    }

    // Remove display math environments
    cleaned = cleaned.replace(
        /\\begin\{(equation|align|align\*)\}[\s\S]*?\\end\{\1\}/g,
        "",
    );

    // Remove figure environments
    cleaned = cleaned.replace(
        /\\begin\{figure\}[\s\S]*?\\end\{figure\}/g,
        "",
    );

    // Remove \begin{enumerate}...\end{enumerate} and \begin{itemize}...\end{itemize}
    // and \begin{description}...\end{description}
    cleaned = cleaned.replace(
        /\\begin\{(enumerate|itemize|description)\}[\s\S]*?\\end\{\1\}/g,
        "",
    );

    // Remove center environments (tables)
    cleaned = cleaned.replace(
        /\\begin\{center\}[\s\S]*?\\end\{center\}/g,
        "",
    );

    // Split on blank lines
    const rawParagraphs = cleaned.split(/\n\s*\n/);
    const paragraphs: string[] = [];

    for (const raw of rawParagraphs) {
        let p = cleanLatex(raw);
        p = wrapInlineMath(p);
        // Skip empty or very short fragments
        if (p.length > 10) {
            paragraphs.push(p);
        }
    }

    return paragraphs;
}

/**
 * Extract all theorem-like environments from a block of text.
 */
function extractTheorems(text: string): PaperTheoremData[] {
    const theorems: PaperTheoremData[] = [];
    const envTypes = [
        "theorem",
        "definition",
        "lemma",
        "proposition",
        "corollary",
        "aside",
        "example",
    ];

    for (const env of envTypes) {
        const re = new RegExp(
            `\\\\begin\\{${env}\\}([\\s\\S]*?)\\\\end\\{${env}\\}`,
            "g",
        );
        let m: RegExpExecArray | null;
        while ((m = re.exec(text)) !== null) {
            const thm = parseTheorem(env, m[1]);
            if (thm) theorems.push(thm);
        }
    }

    return theorems;
}

/** Extract figure environments from a block of text. */
function extractFigures(text: string): PaperFigureData[] {
    const figures: PaperFigureData[] = [];
    const figRe = /\\begin\{figure\}[\s\S]*?\\end\{figure\}/g;
    let m: RegExpExecArray | null;
    while ((m = figRe.exec(text)) !== null) {
        const block = m[0];
        // Extract filename from \includegraphics[...]{filename}
        const fileMatch = block.match(/\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/);
        // Extract caption from \caption{...}
        const capMatch = block.match(/\\caption\{([^}]*(?:\{[^}]*\}[^}]*)*)\}/);
        // Extract label
        const labelMatch = block.match(/\\label\{([^}]*)\}/);

        if (fileMatch) {
            let filename = fileMatch[1];
            // Normalize: remove path prefix, add extension if missing
            filename = filename.replace(/^.*\//, '');
            if (!filename.includes('.')) filename += '.png';
            // Browsers can't render PDF — use PNG version
            filename = filename.replace(/\.pdf$/, '.png');

            figures.push({
                filename,
                caption: capMatch ? cleanLatex(capMatch[1]) : '',
                ...(labelMatch && { label: labelMatch[1] }),
            });
        }
    }
    return figures;
}

/** Interactive callout mapping: section id -> callout config */
const CALLOUTS: Record<string, { text: string; link: string }> = {
    applications: {
        text: "Upload an image and watch epicycles trace its contour",
        link: "/visualize",
    },
    "image-reconstruction-via-epicycles": {
        text: "Try the epicycle reconstruction yourself",
        link: "/visualize",
    },
};

/**
 * Main parser: reads the .tex file and returns structured sections.
 */
function parseLatexPaper(texPath: string): PaperSectionData[] {
    const source = readFileSync(texPath, "utf-8");

    // Find all \chapter, \section, \subsection with their positions
    interface RawSection {
        level: number; // 0 = chapter, 1 = section, 2 = subsection
        title: string;
        startIdx: number;
        endIdx: number; // set later
        content: string; // set later
    }

    const sectionRe =
        /\\(chapter|section|subsection)\*?\{([^}]*)\}/g;
    const rawSections: RawSection[] = [];
    let match: RegExpExecArray | null;

    while ((match = sectionRe.exec(source)) !== null) {
        const levelMap: Record<string, number> = {
            chapter: 0,
            section: 1,
            subsection: 2,
        };
        const level = levelMap[match[1]];
        const title = cleanLatex(match[2]);

        // Skip the Introduction \section (it's level 1 but acts as a chapter)
        rawSections.push({
            level,
            title,
            startIdx: match.index + match[0].length,
            endIdx: source.length,
            content: "",
        });
    }

    // Set end indices
    for (let i = 0; i < rawSections.length; i++) {
        if (i + 1 < rawSections.length) {
            rawSections[i].endIdx = rawSections[i + 1].startIdx;
            // Back up to before the \chapter/\section/\subsection command
            const nextMatch = source.lastIndexOf(
                "\\",
                rawSections[i + 1].startIdx - 1,
            );
            if (nextMatch > rawSections[i].startIdx) {
                rawSections[i].endIdx = nextMatch;
            }
        }
        rawSections[i].content = source.slice(
            rawSections[i].startIdx,
            rawSections[i].endIdx,
        );
    }

    // Build hierarchy: chapters contain sections, sections contain subsections
    // The paper structure: Introduction is a \section before any \chapter
    // Then \chapter{Origin...} contains \section and \subsection children
    // We need to handle this carefully.

    // Strategy: walk through in order, build a flat list with levels,
    // then nest them.

    const topLevel: PaperSectionData[] = [];
    let chapterNum = 0;
    let sectionNum = 0;
    let subsectionNum = 0;

    // Track the "Introduction" which is \section before any \chapter
    let currentChapter: PaperSectionData | null = null;
    let currentSection: PaperSectionData | null = null;

    for (const raw of rawSections) {
        const id = slugify(raw.title);
        const paragraphs = extractParagraphs(raw.content);
        const theorems = extractTheorems(raw.content);
        const figures = extractFigures(raw.content);
        const callout = CALLOUTS[id];

        if (raw.level === 0) {
            // Chapter
            chapterNum++;
            sectionNum = 0;
            subsectionNum = 0;

            currentChapter = {
                id,
                number: String(chapterNum),
                title: raw.title,
                paragraphs,
                ...(theorems.length > 0 && { theorems }),
                ...(figures.length > 0 && { figures }),
                subsections: [],
                ...(callout && { callout }),
            };
            currentSection = null;
            topLevel.push(currentChapter);
        } else if (raw.level === 1) {
            // Section
            if (currentChapter === null) {
                // Pre-chapter section (Introduction)
                chapterNum++;
                sectionNum = 0;
                const section: PaperSectionData = {
                    id,
                    number: String(chapterNum),
                    title: raw.title,
                    paragraphs,
                    ...(theorems.length > 0 && { theorems }),
                    ...(figures.length > 0 && { figures }),
                    ...(callout && { callout }),
                };
                topLevel.push(section);
                // Don't set currentChapter — next \chapter resets
            } else {
                // Section within a chapter
                sectionNum++;
                subsectionNum = 0;
                currentSection = {
                    id,
                    number: `${chapterNum}.${sectionNum}`,
                    title: raw.title,
                    paragraphs,
                    ...(theorems.length > 0 && { theorems }),
                    ...(figures.length > 0 && { figures }),
                    subsections: [],
                    ...(callout && { callout }),
                };
                currentChapter.subsections!.push(currentSection);
            }
        } else if (raw.level === 2) {
            // Subsection — if no section exists yet in this chapter,
            // promote to section level (e.g. \subsection before any \section)
            if (currentChapter && !currentSection) {
                sectionNum++;
                subsectionNum = 0;
                currentSection = {
                    id,
                    number: `${chapterNum}.${sectionNum}`,
                    title: raw.title,
                    paragraphs,
                    ...(theorems.length > 0 && { theorems }),
                    ...(figures.length > 0 && { figures }),
                    subsections: [],
                    ...(callout && { callout }),
                };
                currentChapter.subsections!.push(currentSection);
            } else {
                subsectionNum++;
                const parent = currentSection || currentChapter;
                if (parent) {
                    if (!parent.subsections) parent.subsections = [];
                    parent.subsections.push({
                        id,
                        number: `${chapterNum}.${sectionNum}.${subsectionNum}`,
                        title: raw.title,
                        paragraphs,
                        ...(theorems.length > 0 && { theorems }),
                        ...(figures.length > 0 && { figures }),
                        ...(callout && { callout }),
                    });
                }
            }
        }
    }

    // Clean up: remove empty subsection arrays
    function cleanEmpty(sections: PaperSectionData[]) {
        for (const s of sections) {
            if (s.subsections && s.subsections.length === 0) {
                delete s.subsections;
            } else if (s.subsections) {
                cleanEmpty(s.subsections);
            }
        }
    }
    cleanEmpty(topLevel);

    return topLevel;
}

// ── Vite Plugin ──────────────────────────────────────────────────────

const VIRTUAL_ID = "virtual:paper-content";
const RESOLVED_ID = "\0" + VIRTUAL_ID;

export default function latexPaperPlugin(): Plugin {
    let texPath: string;

    return {
        name: "vite-plugin-latex-paper",
        configResolved(config) {
            // Resolve path to the .tex file relative to project root
            texPath = resolve(config.root, "../paper/fourier_paper.tex");
        },
        resolveId(id) {
            if (id === VIRTUAL_ID) return RESOLVED_ID;
        },
        load(id) {
            if (id !== RESOLVED_ID) return;

            // Watch the .tex file for HMR
            this.addWatchFile(texPath);

            const sections = parseLatexPaper(texPath);

            // Generate the module source
            return [
                `// Auto-generated from fourier_paper.tex — do not edit manually`,
                `export const paperSections = ${JSON.stringify(sections, null, 2)};`,
            ].join("\n");
        },
        handleHotUpdate({ file, server }) {
            if (file === texPath) {
                const mod = server.moduleGraph.getModuleById(RESOLVED_ID);
                if (mod) {
                    server.moduleGraph.invalidateModule(mod);
                    return [mod];
                }
            }
        },
    };
}

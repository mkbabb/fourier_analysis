import type { TreeNode } from "@mkbabb/latex-paper/vue";
import type { PaperSectionData } from "@/lib/paperContent";

export function paperSectionToTreeNode(section: PaperSectionData): TreeNode {
    return {
        id: section.id,
        children: section.subsections?.map(paperSectionToTreeNode),
    };
}

export function getPaperPreview(section: PaperSectionData): string {
    const text = section.content?.find((block): block is string => typeof block === "string") ?? "";
    const clean = text.replace(/\$[^$]+\$/g, "\u2026").replace(/<[^>]+>/g, "");
    const preview = clean.length > 100 ? `${clean.slice(0, 100)}\u2026` : clean;

    const parts: string[] = [];
    if (preview) parts.push(preview);
    if (section.summary) parts.push(section.summary);

    return parts.join(" \u00b7 ");
}

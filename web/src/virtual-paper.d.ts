declare module "virtual:paper-content" {
    import type { PaperSectionData, PaperLabelInfo } from "@mkbabb/latex-paper";
    export const paperSections: PaperSectionData[];
    export const labelMap: Record<string, PaperLabelInfo>;
    export const totalPages: number;
    export const pageMap: Record<string, number>;
}

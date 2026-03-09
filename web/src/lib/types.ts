export interface BasisComponent {
    index: number;
    coefficient: [number, number]; // [re, im]
    amplitude: number;
    phase: number;
}

export interface BasisDecomposition {
    basis: "fourier" | "chebyshev" | "legendre" | string;
    components: BasisComponent[];
    domain: [number, number];
}

export interface AnimationData {
    original: { x: number[]; y: number[] };
    decompositions: Record<string, BasisDecomposition>;
    partial_sums: Record<string, Record<number, { x: number[]; y: number[] }>>;
    eval_points: number[];
    levels: number[];
}

export interface EpicycleData {
    n_components: number;
    components: BasisComponent[];
    trace: { x: number[]; y: number[] };
    path: { x: number[]; y: number[] };
}

export interface ContourData {
    n_contours: number;
    contours: { x: number[]; y: number[]; n_points: number }[];
}

export interface SessionData {
    slug: string;
    created_at: string;
    parameters: ContourSettings;
    animation_settings: AnimationSettings;
    has_image: boolean;
    has_results: boolean;
}

export interface ContourSettings {
    strategy: string;
    resize: number;
    blur_sigma: number;
    n_harmonics: number;
    n_points: number;
    n_classes: number;
    min_contour_length: number;
    min_contour_area: number;
    max_contours: number | null;
    smooth_contours: number;
}

export interface AnimationSettings {
    fps: number;
    duration: number;
    max_circles: number;
}

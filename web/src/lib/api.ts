import type {
    AnimationData,
    ContourData,
    ContourSettings,
    AnimationSettings,
    EpicycleData,
    SessionData,
} from "./types";

const BASE = import.meta.env.VITE_API_URL || "";

/**
 * Per-key AbortController registry. Calling `abortable(key)` cancels any
 * in-flight request for that key and returns a fresh AbortSignal.
 */
const inflight = new Map<string, AbortController>();

function abortable(key: string): AbortSignal {
    inflight.get(key)?.abort();
    const ac = new AbortController();
    inflight.set(key, ac);
    return ac.signal;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (!res.ok) {
        const body = await res.text();
        throw new Error(`API ${res.status}: ${body}`);
    }
    return res.json();
}

/** Check if an error is an abort (not a real failure). */
export function isAbortError(e: unknown): boolean {
    return e instanceof DOMException && e.name === "AbortError";
}

// Sessions
export async function createSession(): Promise<SessionData> {
    return request("/api/sessions", { method: "POST" });
}

export async function getSession(slug: string): Promise<SessionData> {
    return request(`/api/sessions/${slug}`);
}

export async function updateSession(
    slug: string,
    update: {
        parameters?: Partial<ContourSettings>;
        animation_settings?: Partial<AnimationSettings>;
    },
): Promise<SessionData> {
    return request(`/api/sessions/${slug}`, {
        method: "PUT",
        body: JSON.stringify(update),
        signal: abortable("updateSession"),
    });
}

export async function deleteSession(slug: string): Promise<void> {
    return request(`/api/sessions/${slug}`, { method: "DELETE" });
}

// Images
export async function uploadImage(
    slug: string,
    file: File,
): Promise<{ status: string; filename: string; sha256: string; slug?: string; existing?: boolean }> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/api/sessions/${slug}/upload`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
}

export function imageUrl(slug: string): string {
    return `${BASE}/api/sessions/${slug}/image`;
}

// Compute — each endpoint auto-cancels its previous in-flight request
export async function computeContours(
    slug: string,
    params?: Partial<ContourSettings>,
): Promise<ContourData> {
    const res = await request<{ data: ContourData }>(
        `/api/sessions/${slug}/compute/contours`,
        { method: "POST", body: JSON.stringify(params ?? {}), signal: abortable("computeContours") },
    );
    return res.data;
}

export async function computeEpicycles(
    slug: string,
    params?: { n_harmonics?: number; n_points?: number },
): Promise<EpicycleData> {
    const res = await request<{ data: EpicycleData }>(
        `/api/sessions/${slug}/compute/epicycles`,
        { method: "POST", body: JSON.stringify(params ?? {}), signal: abortable("computeEpicycles") },
    );
    return res.data;
}

export async function computeBases(
    slug: string,
    params?: {
        max_degree?: number;
        n_points?: number;
        levels?: number[];
        n_eval?: number;
    },
): Promise<AnimationData> {
    const res = await request<{ data: AnimationData }>(
        `/api/sessions/${slug}/compute/bases`,
        { method: "POST", body: JSON.stringify(params ?? {}), signal: abortable("computeBases") },
    );
    return res.data;
}

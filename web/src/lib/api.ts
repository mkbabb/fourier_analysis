import type {
    AnimationData,
    ContourAsset,
    ContourSettings,
    AnimationSettings,
    EpicycleData,
    ImageMeta,
    Snapshot,
    GalleryEntry,
    GalleryListResponse,
    GalleryTier,
    SessionResponse,
    UserInfo,
    AdminStats,
} from "./types";

const BASE = import.meta.env.VITE_API_URL || "";

// ── Session token management ──

let sessionToken: string | null = null;

export function setSessionToken(token: string | null) {
    sessionToken = token;
}

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

export function abortInflight(keys: string[]) {
    for (const key of keys) {
        inflight.get(key)?.abort();
        inflight.delete(key);
    }
}

/** Check if an error is an abort (not a real failure). */
export function isAbortError(e: unknown): boolean {
    return e instanceof DOMException && e.name === "AbortError";
}

interface ApiFetchOptions extends Omit<RequestInit, "body"> {
    body?: FormData | Record<string, unknown> | BodyInit;
}

async function apiFetch<T>(
    path: string,
    abortKey: string,
    options?: ApiFetchOptions,
): Promise<T> {
    const headers: Record<string, string> = {
        ...((options?.headers as Record<string, string>) ?? {}),
    };

    if (sessionToken) {
        headers["X-Session-Token"] = sessionToken;
    }

    const rawBody = options?.body;
    const isFormData = rawBody instanceof FormData;

    // FormData: let browser set Content-Type with boundary
    // Plain object: set JSON content type and stringify
    // No body: no content type
    let body: BodyInit | undefined;
    if (isFormData) {
        body = rawBody;
    } else if (rawBody != null && typeof rawBody === "object" && !(rawBody instanceof Blob) && !(rawBody instanceof ArrayBuffer) && !(rawBody instanceof ReadableStream)) {
        headers["Content-Type"] ??= "application/json";
        body = JSON.stringify(rawBody);
    } else {
        body = rawBody as BodyInit | undefined;
    }

    const res = await fetch(`${BASE}${path}`, {
        method: options?.method,
        headers,
        body,
        signal: options?.signal ?? abortable(abortKey),
    });

    if (!res.ok) {
        let text: string;
        try {
            text = await res.text();
        } catch {
            text = "(could not read response body)";
        }
        throw new Error(`API ${res.status}: ${text}`);
    }

    try {
        return await res.json();
    } catch {
        throw new Error(`API ${res.status}: invalid JSON response`);
    }
}

async function adminFetch<T>(
    path: string,
    adminToken: string,
    options?: ApiFetchOptions,
): Promise<T> {
    const headers: Record<string, string> = {
        Authorization: `Bearer ${adminToken}`,
        ...((options?.headers as Record<string, string>) ?? {}),
    };

    if (sessionToken) {
        headers["X-Session-Token"] = sessionToken;
    }

    const rawBody = options?.body;
    const isFormData = rawBody instanceof FormData;

    let body: BodyInit | undefined;
    if (isFormData) {
        body = rawBody;
    } else if (rawBody != null && typeof rawBody === "object" && !(rawBody instanceof Blob) && !(rawBody instanceof ArrayBuffer) && !(rawBody instanceof ReadableStream)) {
        headers["Content-Type"] ??= "application/json";
        body = JSON.stringify(rawBody);
    } else {
        body = rawBody as BodyInit | undefined;
    }

    const res = await fetch(`${BASE}${path}`, {
        method: options?.method,
        headers,
        body,
    });

    if (!res.ok) {
        let text: string;
        try {
            text = await res.text();
        } catch {
            text = "(could not read response body)";
        }
        throw new Error(`API ${res.status}: ${text}`);
    }

    try {
        return await res.json();
    } catch {
        throw new Error(`API ${res.status}: invalid JSON response`);
    }
}

// ── Images ──

export async function computeSha256(file: File): Promise<string> {
    const buf = await file.arrayBuffer();
    const hash = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

export async function checkImageHash(hash: string): Promise<ImageMeta | null> {
    const res = await fetch(`${BASE}/api/images/by-hash/${hash}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`Hash check failed: ${res.status}`);
    return res.json();
}

export async function uploadImage(file: File): Promise<ImageMeta> {
    const form = new FormData();
    form.append("file", file);
    return apiFetch<ImageMeta>("/api/images", "uploadImage", {
        method: "POST",
        body: form,
    });
}

export async function getImageMeta(imageSlug: string): Promise<ImageMeta> {
    return apiFetch<ImageMeta>(`/api/images/${imageSlug}`, "getImageMeta");
}

export function imageUrl(imageSlug: string): string {
    return `${BASE}/api/images/${imageSlug}/blob`;
}

export function thumbnailUrl(imageSlug: string): string {
    return `${BASE}/api/images/${imageSlug}/thumbnail`;
}

export function overlayUrl(imageSlug: string, resize: number = 768): string {
    return `${BASE}/api/images/${imageSlug}/overlay?resize=${resize}`;
}

export async function extractContour(
    imageSlug: string,
    settings: ContourSettings,
): Promise<ContourAsset> {
    return apiFetch<ContourAsset>(
        `/api/images/${imageSlug}/extract-contour`,
        "extractContour",
        {
            method: "POST",
            body: { ...settings },
        },
    );
}

// ── Contours ──

export async function saveContour(
    imageSlug: string,
    points: { x: number[]; y: number[] },
): Promise<ContourAsset> {
    return apiFetch<ContourAsset>("/api/contours", "saveContour", {
        method: "POST",
        body: { image_slug: imageSlug, points },
    });
}

export async function getContour(contourHash: string): Promise<ContourAsset> {
    return apiFetch<ContourAsset>(`/api/contours/${contourHash}`, "getContour");
}

export async function computeEpicycles(
    contourHash: string,
    params: { n_harmonics: number; n_points: number },
): Promise<EpicycleData> {
    const res = await apiFetch<{ data: EpicycleData }>(
        `/api/contours/${contourHash}/compute/epicycles`,
        "computeEpicycles",
        {
            method: "POST",
            body: { ...params },
        },
    );
    return res.data;
}

export async function computeBases(
    contourHash: string,
    params: {
        max_degree: number;
        n_points: number;
        levels: number[];
        n_eval: number;
    },
): Promise<AnimationData> {
    const res = await apiFetch<{ data: AnimationData }>(
        `/api/contours/${contourHash}/compute/bases`,
        "computeBases",
        {
            method: "POST",
            body: { ...params },
        },
    );
    return res.data;
}

// ── Snapshots ──

export async function saveSnapshot(
    imageSlug: string,
    req: {
        contour_hash: string;
        contour_settings: ContourSettings;
        animation_settings: AnimationSettings;
    },
): Promise<Snapshot> {
    return apiFetch<Snapshot>(
        `/api/images/${imageSlug}/snapshots`,
        "saveSnapshot",
        {
            method: "POST",
            body: { ...req },
        },
    );
}

export async function getSnapshot(
    imageSlug: string,
    snapshotHash: string,
): Promise<Snapshot> {
    return apiFetch<Snapshot>(
        `/api/images/${imageSlug}/snapshots/${snapshotHash}`,
        "getSnapshot",
    );
}

// ── Sessions ──

export async function createSession(): Promise<SessionResponse> {
    return apiFetch<SessionResponse>("/api/sessions", "createSession", {
        method: "POST",
    });
}

export async function loginWithSlug(slug: string): Promise<SessionResponse> {
    return apiFetch<SessionResponse>("/api/sessions/login", "loginWithSlug", {
        method: "POST",
        body: { slug },
    });
}

export async function getMe(): Promise<UserInfo> {
    return apiFetch<UserInfo>("/api/sessions/me", "getMe");
}

export async function deleteSession(): Promise<{ ok: boolean }> {
    return apiFetch<{ ok: boolean }>("/api/sessions", "deleteSession", {
        method: "DELETE",
    });
}

// ── Gallery ──

export async function listGallery(params: {
    page?: number;
    limit?: number;
    sort?: string;
    tier?: GalleryTier;
    q?: string;
    basis?: string;
}): Promise<GalleryListResponse> {
    const qs = new URLSearchParams();
    if (params.page != null) qs.set("page", String(params.page));
    if (params.limit != null) qs.set("limit", String(params.limit));
    if (params.sort) qs.set("sort", params.sort);
    if (params.tier) qs.set("tier", params.tier);
    if (params.q) qs.set("q", params.q);
    if (params.basis) qs.set("basis", params.basis);
    const query = qs.toString();
    return apiFetch<GalleryListResponse>(
        `/api/gallery${query ? `?${query}` : ""}`,
        "listGallery",
    );
}

export async function getGalleryEntry(hash: string): Promise<GalleryEntry> {
    return apiFetch<GalleryEntry>(`/api/gallery/${hash}`, "getGalleryEntry");
}

export async function publishToGallery(
    snapshotHash: string,
    imageSlug: string,
): Promise<GalleryEntry> {
    return apiFetch<GalleryEntry>("/api/gallery", "publishToGallery", {
        method: "POST",
        body: { snapshot_hash: snapshotHash, image_slug: imageSlug },
    });
}

export async function recordView(hash: string): Promise<{ views: number }> {
    return apiFetch<{ views: number }>(
        `/api/gallery/${hash}/view`,
        "recordView",
        { method: "POST" },
    );
}

export async function toggleLike(
    hash: string,
): Promise<{ liked: boolean; likes: number }> {
    return apiFetch<{ liked: boolean; likes: number }>(
        `/api/gallery/${hash}/like`,
        "toggleLike",
        { method: "POST" },
    );
}

// ── Admin ──

export async function verifyAdmin(
    token: string,
): Promise<{ ok: boolean }> {
    return adminFetch<{ ok: boolean }>("/api/admin/verify", token);
}

export async function getAdminStats(token: string): Promise<AdminStats> {
    return adminFetch<AdminStats>("/api/admin/stats", token);
}

export async function setGalleryTier(
    token: string,
    hash: string,
    tier: GalleryTier,
): Promise<GalleryEntry> {
    return adminFetch<GalleryEntry>(`/api/admin/gallery/${hash}/tier`, token, {
        method: "PUT",
        body: { tier },
    });
}

export async function deleteGalleryEntry(
    token: string,
    hash: string,
): Promise<{ ok: boolean }> {
    return adminFetch<{ ok: boolean }>(`/api/admin/gallery/${hash}`, token, {
        method: "DELETE",
    });
}

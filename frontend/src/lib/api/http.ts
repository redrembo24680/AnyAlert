import { env } from "@/lib/config/env";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    let authorizationHeader: Record<string, string> = {};

    if (typeof window !== "undefined") {
        const session = window.localStorage.getItem("anyalert:session");
        if (session) {
            try {
                const parsed = JSON.parse(session) as { token?: string };
                if (parsed.token) {
                    authorizationHeader = { Authorization: `Bearer ${parsed.token}` };
                }
            } catch {
                // Ignore malformed session data and continue without auth headers.
            }
        }
    }

    const response = await fetch(`${env.apiUrl}${path}`, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...authorizationHeader,
            ...(init?.headers ?? {})
        },
        cache: "no-store"
    });

    if (!response.ok) {
        const details = await response.text();
        throw new Error(`API ${response.status}: ${details}`);
    }

    return (await response.json()) as T;
}

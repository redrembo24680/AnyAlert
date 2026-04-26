import type { AuthResponse, LoginPayload } from "@/shared/types/api";

import { apiFetch } from "@/lib/api/http";

export async function login(payload: LoginPayload): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload)
    });
}

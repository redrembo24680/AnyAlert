import type { RegisterPayload, RegisterResponse } from "@/shared/types/api";

import { apiFetch } from "@/lib/api/http";

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
    return apiFetch<RegisterResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload)
    });
}

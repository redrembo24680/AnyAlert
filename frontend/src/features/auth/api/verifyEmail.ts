import type { VerifyEmailPayload, VerifyEmailResponse } from "@/shared/types/api";

import { apiFetch } from "@/lib/api/http";

export async function verifyEmail(payload: VerifyEmailPayload): Promise<VerifyEmailResponse> {
    return apiFetch<VerifyEmailResponse>("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify(payload)
    });
}

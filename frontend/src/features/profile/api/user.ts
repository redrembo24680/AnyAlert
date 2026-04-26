import type { UserReadResponse, UserUpdatePayload } from "@/shared/types/api";
import { apiFetch } from "@/lib/api/http";

export async function getMe(token: string): Promise<UserReadResponse> {
    return apiFetch<UserReadResponse>("/users/me", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
}

export async function updateMe(payload: UserUpdatePayload, token: string): Promise<UserReadResponse> {
    return apiFetch<UserReadResponse>("/users/me", {
        method: "PATCH",
        headers: {
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });
}

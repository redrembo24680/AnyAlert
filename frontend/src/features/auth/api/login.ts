import type { AuthResponse, LoginPayload } from "@/shared/types/api";

import { mockLogin } from "@/features/auth/api/mockAuthStore";

export async function login(payload: LoginPayload): Promise<AuthResponse> {
    return mockLogin(payload);
}

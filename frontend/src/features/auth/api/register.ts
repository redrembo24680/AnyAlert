import type { AuthResponse, RegisterPayload } from "@/shared/types/api";

import { mockRegister } from "@/features/auth/api/mockAuthStore";

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
    return mockRegister(payload);
}

import type { LoginPayload } from "@/shared/types/api";

export async function login(_payload: LoginPayload): Promise<void> {
  // Placeholder for real auth integration (JWT/cookie flow).
  return Promise.resolve();
}

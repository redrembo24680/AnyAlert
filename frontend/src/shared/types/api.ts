export interface HealthResponse {
    status: "ok" | "error";
}

export interface LoginPayload {
    email: string;
    password: string;
}

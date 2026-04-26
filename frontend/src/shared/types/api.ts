export interface HealthResponse {
    status: "ok" | "error";
}

export interface LoginPayload {
    email: string;
    password: string;
}

export interface RegisterPayload {
    name: string;
    email: string;
    password: string;
}

export interface AuthUser {
    name: string;
    email: string;
}

export interface AuthResponse {
    token: string;
    user: AuthUser;
}

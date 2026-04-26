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

export interface RegisterResponse {
    message: string;
    verification_required: boolean;
    dev_verification_code?: string | null;
}

export interface VerifyEmailPayload {
    email: string;
    code: string;
}

export interface VerifyEmailResponse {
    message: string;
    token: string;
    user: AuthUser;
}

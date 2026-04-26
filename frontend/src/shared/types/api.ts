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
export interface TrackerCreatePayload {
    url: string;
    network: string;
    trigger_type: string;
    trigger_value?: number | null;
}

export interface TrackerResponse {
    id: number;
    user_id: number;
    url: string;
    network: string;
    title: string | null;
    trigger_type: string;
    trigger_value: number | null;
    last_price: number | null;
    last_status: string | null;
    last_checked_at: string | null;
    is_active: boolean;
    created_at: string;
}
export interface UserUpdatePayload {
    full_name?: string;
    email?: string;
}

export interface UserReadResponse {
    id: number;
    email: string;
    full_name: string | null;
    is_email_verified: boolean;
    created_at: string;
}

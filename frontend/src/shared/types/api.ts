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
    last_old_price?: number | null;
    last_discount_percent?: number | null;
    last_rating?: number | null;
    last_views?: number | null;
    last_reviews_count?: number | null;
    last_cashback_amount?: number | null;
    last_trade_in_available?: boolean | null;
    last_credit_available?: boolean | null;
    last_delivery_available?: boolean | null;
    last_pickup_available?: boolean | null;
    last_personal_price_available?: boolean | null;
    last_gift_offer_available?: boolean | null;
    last_color?: string | null;
    last_memory_variant?: string | null;
    last_availability?: boolean | null;
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

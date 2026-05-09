import { apiFetch } from "@/lib/api/http";
import type {
    AuthResponse,
    TelegramLinkCodeResponse,
    TelegramStatusResponse,
    TelegramWidgetUser,
} from "@/shared/types/api";

/** Login or register via Telegram Login Widget data */
export async function telegramLogin(data: TelegramWidgetUser): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/auth/telegram", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

/** Generate a link code to connect Telegram bot to an existing account */
export async function generateLinkCode(): Promise<TelegramLinkCodeResponse> {
    return apiFetch<TelegramLinkCodeResponse>("/telegram/link-code", { method: "POST" });
}

/** Get current Telegram link status */
export async function getTelegramStatus(): Promise<TelegramStatusResponse> {
    return apiFetch<TelegramStatusResponse>("/telegram/status");
}

/** Unlink Telegram from current account */
export async function unlinkTelegram(): Promise<void> {
    await apiFetch<void>("/telegram/unlink", { method: "DELETE" });
}

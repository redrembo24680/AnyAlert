"use client";

import { useEffect, useRef } from "react";
import type { TelegramWidgetUser } from "@/shared/types/api";

interface TelegramLoginButtonProps {
    botUsername: string;
    onAuth: (user: TelegramWidgetUser) => void;
    buttonSize?: "large" | "medium" | "small";
    requestAccess?: boolean;
}

declare global {
    interface Window {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        TelegramLoginCallback?: (user: TelegramWidgetUser) => void;
    }
}

export function TelegramLoginButton({
    botUsername,
    onAuth,
    buttonSize = "large",
    requestAccess = true,
}: TelegramLoginButtonProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Expose callback globally (Telegram widget calls window.TelegramLoginCallback)
        window.TelegramLoginCallback = onAuth;

        // Remove any previously injected script/widget
        containerRef.current.innerHTML = "";

        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-widget.js?22";
        script.setAttribute("data-telegram-login", botUsername);
        script.setAttribute("data-size", buttonSize);
        script.setAttribute("data-onauth", "TelegramLoginCallback(user)");
        script.setAttribute("data-request-access", requestAccess ? "write" : "read");
        script.async = true;

        containerRef.current.appendChild(script);

        return () => {
            delete window.TelegramLoginCallback;
        };
    // botUsername and buttonSize won't change at runtime, so exhaustive deps don't matter here
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [botUsername]);

    return <div ref={containerRef} className="tg-widget-wrap" />;
}

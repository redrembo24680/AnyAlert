"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useRef, useState, useEffect, KeyboardEvent, ClipboardEvent } from "react";

import { verifyEmail } from "@/features/auth/api/verifyEmail";
import { useAuth } from "@/features/auth/contexts/AuthContext";

export function VerifyEmailForm() {
    const router = useRouter();
    const { login } = useAuth();
    const searchParams = useSearchParams();
    const email = searchParams.get("email") ?? "";
    const devCode = searchParams.get("code") ?? "";

    const [digits, setDigits] = useState<string[]>(() => {
        if (devCode.length === 6 && /^\d{6}$/.test(devCode)) {
            return devCode.split("");
        }
        return ["", "", "", "", "", ""];
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<string | null>(
        devCode ? `Dev-код автоматично заповнено: ${devCode}` : null
    );
    const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

    useEffect(() => {
        inputsRef.current[0]?.focus();
    }, []);

    function handleChange(index: number, value: string) {
        if (!/^\d*$/.test(value)) return;

        const next = [...digits];
        next[index] = value.slice(-1);
        setDigits(next);

        if (value && index < 5) {
            inputsRef.current[index + 1]?.focus();
        }
    }

    function handleKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Backspace" && !digits[index] && index > 0) {
            inputsRef.current[index - 1]?.focus();
        }
    }

    function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
        event.preventDefault();
        const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
        if (!pasted) return;

        const next = [...digits];
        for (let i = 0; i < 6; i++) {
            next[i] = pasted[i] ?? "";
        }
        setDigits(next);

        const focusIndex = Math.min(pasted.length, 5);
        inputsRef.current[focusIndex]?.focus();
    }

    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        const code = digits.join("");
        if (code.length !== 6) {
            setMessage("Введіть усі 6 цифр");
            return;
        }

        setIsSubmitting(true);
        setMessage(null);

        try {
            const response = await verifyEmail({ email, code });
            login({ token: response.token, user: response.user });
            setMessage("Email підтверджено! Входимо в акаунт...");
            setTimeout(() => router.push("/"), 1500);
        } catch (error) {
            if (error instanceof Error) {
                setMessage(error.message);
            } else {
                setMessage("Не вдалося підтвердити. Спробуйте ще раз.");
            }
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form className="auth-form" onSubmit={onSubmit}>
            <p className="verify-email-hint">
                Код надіслано на <strong>{email || "вашу пошту"}</strong>
            </p>

            <div className="verify-code-inputs">
                {digits.map((digit, index) => (
                    <input
                        key={index}
                        ref={(el) => { inputsRef.current[index] = el; }}
                        id={`verifyDigit${index}`}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleChange(index, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(index, e)}
                        onPaste={index === 0 ? handlePaste : undefined}
                        className="verify-digit-input"
                        autoComplete="one-time-code"
                        required
                    />
                ))}
            </div>

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Перевіряємо..." : "Підтвердити"}
            </button>

            {message ? <p className="form-message">{message}</p> : null}
        </form>
    );
}

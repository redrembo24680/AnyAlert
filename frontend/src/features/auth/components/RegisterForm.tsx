"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { register } from "@/features/auth/api/register";
import { telegramLogin } from "@/features/auth/api/telegram";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { TelegramLoginButton } from "@/features/auth/components/TelegramLoginButton";
import type { TelegramWidgetUser } from "@/shared/types/api";

const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME ?? "";

export function RegisterForm() {
    const router = useRouter();
    const { login } = useAuth();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        if (password !== confirmPassword) {
            setMessage("Паролі не співпадають");
            return;
        }

        setIsSubmitting(true);
        setMessage(null);

        try {
            const response = await register({ name, email, password });
            let verifyUrl = `/verify-email?email=${encodeURIComponent(email)}`;
            if (response.dev_verification_code) {
                verifyUrl += `&code=${encodeURIComponent(response.dev_verification_code)}`;
            }
            router.push(verifyUrl);
        } catch (error) {
            if (error instanceof Error) {
                setMessage(error.message);
            } else {
                setMessage("Не вдалося зареєструватися. Спробуйте ще раз.");
            }
        } finally {
            setIsSubmitting(false);
        }
    }

    async function onTelegramAuth(tgUser: TelegramWidgetUser) {
        setMessage(null);
        try {
            const response = await telegramLogin(tgUser);
            login(response);
            router.push("/");
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Не вдалося зареєструватися через Telegram.");
        }
    }

    return (
        <>
            {BOT_USERNAME && (
                <div className="tg-register-section">
                    <p className="tg-register-hint">Швидка реєстрація через Telegram — без паролю:</p>
                    <TelegramLoginButton botUsername={BOT_USERNAME} onAuth={onTelegramAuth} />
                    <div className="auth-divider"><span>або зареєструйтесь через email</span></div>
                </div>
            )}

            <form className="auth-form" onSubmit={onSubmit}>
                <label htmlFor="registerName">Імʼя</label>
                <input
                    id="registerName"
                    type="text"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Ваше імʼя"
                    required
                />

                <label htmlFor="registerEmail">Email</label>
                <input
                    id="registerEmail"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                />

                <label htmlFor="registerPassword">Пароль</label>
                <input
                    id="registerPassword"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Придумайте пароль"
                    minLength={6}
                    required
                />

                <label htmlFor="registerConfirmPassword">Підтвердіть пароль</label>
                <input
                    id="registerConfirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Повторіть пароль"
                    minLength={6}
                    required
                />

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Створюємо..." : "Створити акаунт"}
                </button>

                {message ? <p className="form-message">{message}</p> : null}

                <p className="auth-helper">
                    Вже маєте акаунт? <Link href="/login">Увійти</Link>
                </p>
            </form>
        </>
    );
}

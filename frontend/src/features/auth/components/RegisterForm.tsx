"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { register } from "@/features/auth/api/register";

export function RegisterForm() {
    const router = useRouter();
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

    return (
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
    );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { login as loginApi } from "@/features/auth/api/login";
import { useAuth } from "@/features/auth/contexts/AuthContext";

export function LoginForm() {
    const router = useRouter();
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSubmitting(true);
        setMessage(null);

        try {
            const response = await loginApi({ email, password });
            login(response);
            setMessage("Вхід успішний. Повертаємо на головну...");
            router.push("/");
        } catch (error) {
            if (error instanceof Error) {
                setMessage(error.message);
            } else {
                setMessage("Не вдалося увійти. Спробуйте ще раз.");
            }
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form className="auth-form" onSubmit={onSubmit}>
            <label htmlFor="loginEmail">Email</label>
            <input
                id="loginEmail"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
            />

            <label htmlFor="loginPassword">Пароль</label>
            <input
                id="loginPassword"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Введіть пароль"
                required
            />

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Входимо..." : "Увійти"}
            </button>

            {message ? <p className="form-message">{message}</p> : null}

            <p className="auth-helper">
                Ще не маєте акаунта? <Link href="/register">Створити акаунт</Link>
            </p>
        </form>
    );
}

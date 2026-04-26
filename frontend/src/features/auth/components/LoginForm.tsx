"use client";

import { FormEvent, useState } from "react";

import { login } from "@/features/auth/api/login";

export function LoginForm() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState<string | null>(null);

    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        try {
            await login({ email, password });
            setMessage("Success");
        } catch {
            setMessage("Login failed");
        }
    }

    return (
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, maxWidth: 320 }}>
            <label>
                Email
                <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                />
            </label>
            <label>
                Password
                <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                />
            </label>
            <button type="submit">Sign in</button>
            {message ? <p>{message}</p> : null}
        </form>
    );
}

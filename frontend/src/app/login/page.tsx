"use client";

import { Card } from "@/components/ui/Card";
import { GuestOnlyGate } from "@/features/auth/components/GuestOnlyGate";
import { LoginForm } from "@/features/auth/components/LoginForm";

export default function LoginPage() {
    return (
        <GuestOnlyGate>
            <section className="auth-page">
                <Card
                    className="auth-card"
                    title="Вхід в AnyAlert"
                    description="Увійдіть у ваш акаунт, щоб керувати відстеженням товарів."
                >
                    <LoginForm />
                </Card>
            </section>
        </GuestOnlyGate>
    );
}

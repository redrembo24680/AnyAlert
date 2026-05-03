"use client";

import { Card } from "@/components/ui/Card";
import { GuestOnlyGate } from "@/features/auth/components/GuestOnlyGate";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export default function RegisterPage() {
    return (
        <GuestOnlyGate>
            <section className="auth-page">
                <Card
                    className="auth-card"
                    title="Створити акаунт"
                    description="Зареєструйтесь, щоб додавати посилання на товари й отримувати автоматичний моніторинг."
                >
                    <RegisterForm />
                </Card>
            </section>
        </GuestOnlyGate>
    );
}

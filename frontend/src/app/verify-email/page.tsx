import { Suspense } from "react";

import { Card } from "@/components/ui/Card";
import { VerifyEmailForm } from "@/features/auth/components/VerifyEmailForm";

export default function VerifyEmailPage() {
    return (
        <section className="auth-page">
            <Card
                className="auth-card"
                title="Підтвердження email"
                description="Введіть 6-значний код, який ми надіслали на вашу електронну пошту."
            >
                <Suspense fallback={<p>Завантаження...</p>}>
                    <VerifyEmailForm />
                </Suspense>
            </Card>
        </section>
    );
}

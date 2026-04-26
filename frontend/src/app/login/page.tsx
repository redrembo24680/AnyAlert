import { Card } from "@/components/ui/Card";
import { LoginForm } from "@/features/auth/components/LoginForm";

export default function LoginPage() {
    return (
        <section className="auth-page">
            <Card
                className="auth-card"
                title="Вхід в AnyAlert"
                description="Увійдіть у ваш акаунт, щоб керувати відстеженням товарів."
            >
                <LoginForm />
            </Card>
        </section>
    );
}

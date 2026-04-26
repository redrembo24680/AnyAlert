import { Card } from "@/components/ui/Card";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export default function RegisterPage() {
    return (
        <section className="auth-page">
            <Card
                className="auth-card"
                title="Створити акаунт"
                description="Зареєструйтесь, щоб додавати посилання на товари й отримувати автоматичний моніторинг."
            >
                <RegisterForm />
            </Card>
        </section>
    );
}

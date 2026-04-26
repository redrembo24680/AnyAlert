import { LoginForm } from "@/features/auth/components/LoginForm";

export default function HomePage() {
    return (
        <main>
            <h1>AnyAlert</h1>
            <p>Scalable Next.js architecture with feature modules and API boundary.</p>
            <LoginForm />
        </main>
    );
}

"use client";

import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { useAuth } from "@/features/auth/contexts/AuthContext";

export default function HomePage() {
    const { isAuthenticated, user } = useAuth();

    return (
        <section className="landing">
            <div className="hero">
                <p className="hero-kicker">AnyAlert</p>
                <h1>
                    {isAuthenticated
                        ? `Вітаємо${user?.name ? `, ${user.name}` : ""} — ваш моніторинг уже активний`
                        : "Ми допомагаємо економити ваш час на автоматизації моніторингу товарів"}
                </h1>
                <p className="hero-description">
                    {isAuthenticated
                        ? "Перейдіть до профілю, щоб керувати товарами, переглядати трекери й оновлювати налаштування без зайвих кроків."
                        : "Ви надсилаєте нам посилання на потрібний товар, а ми автоматично відслідковуємо зміни. Замість ручної перевірки магазинів ви отримуєте зручний контроль в одному місці."}
                </p>
                <div className="hero-actions">
                    {isAuthenticated ? (
                        <>
                            <Link href="/profile" className="button-primary">
                                Відкрити профіль
                            </Link>
                            <Link href="/platforms" className="button-ghost">
                                Додати товар
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link href="/register" className="button-primary">
                                Почати безкоштовно
                            </Link>
                            <Link href="/login" className="button-ghost">
                                Увійти
                            </Link>
                        </>
                    )}
                </div>
            </div>

            <div className="steps-grid">
                {isAuthenticated ? (
                    <>
                        <Card
                            title="1. Профіль під рукою"
                            description="Керуйте даними акаунта та швидко переходьте до своїх налаштувань."
                        />
                        <Card
                            title="2. Треки вже працюють"
                            description="Відкривайте платформи й додавайте нові товари без повторної авторизації."
                        />
                        <Card
                            title="3. Менше ручної рутини"
                            description="Усі дії зібрані в одному місці, щоб не витрачати час на повторні входи."
                        />
                    </>
                ) : (
                    <>
                        <Card
                            title="1. Надішліть посилання"
                            description="Додаєте URL товару, який хочете відстежувати."
                        />
                        <Card
                            title="2. Автоматичний перегляд"
                            description="Система сама перевіряє сторінки без ручного моніторингу."
                        />
                        <Card
                            title="3. Ви економите час"
                            description="Менше рутини, більше часу на важливі задачі та рішення."
                        />
                    </>
                )}
            </div>

            <Card
                className="demo-card"
                title={isAuthenticated ? "Ваш акаунт готовий до роботи" : "Працюємо з багатьма платформами"}
                description={
                    isAuthenticated
                        ? "Відкрийте профіль або перейдіть до платформ, щоб додати перший товар і налаштувати моніторинг."
                        : "Вставка посилань та налаштування тригерів винесені в окремий розділ з маркетплейсами."
                }
            >
                <div className="hero-actions">
                    {isAuthenticated ? (
                        <>
                            <Link href="/profile" className="button-primary">
                                До профілю
                            </Link>
                            <Link href="/platforms" className="button-ghost">
                                До платформ
                            </Link>
                        </>
                    ) : (
                        <Link href="/platforms" className="button-primary">
                            Перейти до платформ
                        </Link>
                    )}
                </div>
            </Card>
        </section>
    );
}

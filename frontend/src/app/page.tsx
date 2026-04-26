import Link from "next/link";

import { Card } from "@/components/ui/Card";

export default function HomePage() {
    return (
        <section className="landing">
            <div className="hero">
                <p className="hero-kicker">AnyAlert</p>
                <h1>Ми допомагаємо економити ваш час на автоматизації моніторингу товарів</h1>
                <p className="hero-description">
                    Ви надсилаєте нам посилання на потрібний товар, а ми автоматично відслідковуємо зміни.
                    Замість ручної перевірки магазинів ви отримуєте зручний контроль в одному місці.
                </p>
                <div className="hero-actions">
                    <Link href="/register" className="button-primary">
                        Почати безкоштовно
                    </Link>
                    <Link href="/login" className="button-ghost">
                        Увійти
                    </Link>
                </div>
            </div>

            <div className="steps-grid">
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
            </div>

            <Card
                className="demo-card"
                title="Працюємо з багатьма платформами"
                description="Вставка посилань та налаштування тригерів винесені в окремий розділ з маркетплейсами."
            >
                <div className="hero-actions">
                    <Link href="/platforms" className="button-primary">
                        Перейти до платформ
                    </Link>
                </div>
            </Card>
        </section>
    );
}

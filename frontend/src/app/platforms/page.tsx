import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { marketplacePlatforms } from "@/features/tracking/data/platforms";

export default function PlatformsPage() {
    return (
        <section className="platforms-page">
            <header className="platforms-header">
                <p className="hero-kicker">Маркетплейси</p>
                <h1>Оберіть платформу для відстеження товарів</h1>
                <p>
                    Ми можемо працювати з багатьма сайтами одночасно. Виберіть потрібний сервіс,
                    відкрийте його сторінку та додайте посилання на товар з тригером сповіщення.
                </p>
            </header>

            <div className="platforms-grid">
                {marketplacePlatforms.map((platform) => (
                    <Card key={platform.slug} className="platform-card">
                        <div className="platform-card-head">
                            <span
                                className="platform-badge"
                                style={{
                                    backgroundColor: platform.accentSoft,
                                    color: platform.accent
                                }}
                            >
                                {platform.name}
                            </span>
                            <h3>{platform.name}</h3>
                        </div>

                        <p>{platform.shortDescription}</p>

                        <Link href={`/platforms/${platform.slug}`} className="button-primary platform-link">
                            Відкрити сторінку {platform.name}
                        </Link>
                    </Card>
                ))}
            </div>
        </section>
    );
}

import Link from "next/link";
import { notFound } from "next/navigation";

import { Card } from "@/components/ui/Card";
import { PlatformTrackingForm } from "@/features/tracking/components/PlatformTrackingForm";
import { findPlatformBySlug, marketplacePlatforms } from "@/features/tracking/data/platforms";

interface PlatformPageProps {
    params: {
        slug: string;
    };
}

export function generateStaticParams() {
    return marketplacePlatforms.map((platform) => ({ slug: platform.slug }));
}

export default function PlatformPage({ params }: PlatformPageProps) {
    const platform = findPlatformBySlug(params.slug);

    if (!platform) {
        notFound();
    }

    return (
        <section className="platform-detail-page">
            <div
                className="platform-hero"
                style={{
                    background: `linear-gradient(145deg, ${platform.bannerFrom} 0%, ${platform.bannerTo} 100%)`,
                    borderColor: platform.accentSoft
                }}
            >
                <p className="hero-kicker" style={{ color: platform.accent }}>
                    {platform.name}
                </p>
                <h1>Налаштуйте відстеження товару на {platform.name}</h1>
                <p>{platform.longDescription}</p>
            </div>

            <Card className="platform-form-card">
                <PlatformTrackingForm platform={platform} />
            </Card>

            <div className="platform-actions">
                <Link href="/platforms" className="button-ghost">
                    Повернутись до всіх платформ
                </Link>
            </div>
        </section>
    );
}

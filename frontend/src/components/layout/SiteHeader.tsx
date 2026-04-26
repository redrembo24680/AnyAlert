import Link from "next/link";

export function SiteHeader() {
    return (
        <header className="site-header">
            <div className="site-header-inner">
                <Link href="/" className="brand-link">
                    AnyAlert
                </Link>
                <nav className="site-nav" aria-label="Головна навігація">
                    <Link href="/">Головна</Link>
                    <Link href="/platforms">Платформи</Link>
                    <Link href="/login">Увійти</Link>
                    <Link href="/register" className="nav-cta">
                        Реєстрація
                    </Link>
                </nav>
            </div>
        </header>
    );
}

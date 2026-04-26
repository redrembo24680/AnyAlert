"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/contexts/AuthContext";

export function SiteHeader() {
    const { isAuthenticated, user, logout } = useAuth();
    const router = useRouter();

    const handleLogout = () => {
        logout();
        router.push("/");
    };

    return (
        <header className="site-header">
            <div className="site-header-inner">
                <Link href="/" className="brand-link">
                    AnyAlert
                </Link>
                <nav className="site-nav" aria-label="Головна навігація">
                    <Link href="/">Головна</Link>
                    <Link href="/platforms">Платформи</Link>
                    
                    {isAuthenticated ? (
                        <>
                            <span className="user-greeting" style={{marginRight: '8px', color: 'var(--text)', fontWeight: 600}}>
                                {user?.name}
                            </span>
                            <button onClick={handleLogout} className="button-ghost" style={{padding: '6px 12px', fontSize: '0.9rem'}}>
                                Вийти
                            </button>
                        </>
                    ) : (
                        <>
                            <Link href="/login">Увійти</Link>
                            <Link href="/register" className="nav-cta">
                                Реєстрація
                            </Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}

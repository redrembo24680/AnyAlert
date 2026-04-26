import type { Metadata } from "next";
import "./globals.css";

import { SiteHeader } from "@/components/layout/SiteHeader";

export const metadata: Metadata = {
    title: "AnyAlert",
    description: "Сервіс автоматизації моніторингу товарів за посиланням"
};

export default function RootLayout({
    children
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="uk">
            <body>
                <div className="app-shell">
                    <SiteHeader />
                    <main className="page-container">{children}</main>
                    <footer className="site-footer">AnyAlert · Автоматизація рутини для вашого часу</footer>
                </div>
            </body>
        </html>
    );
}

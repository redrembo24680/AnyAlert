import { PropsWithChildren } from "react";

export function Card({ children }: PropsWithChildren) {
    return (
        <section
            style={{
                border: "1px solid var(--border)",
                background: "var(--surface)",
                borderRadius: 12,
                padding: 16
            }}
        >
            {children}
        </section>
    );
}

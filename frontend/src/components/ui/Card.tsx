import { PropsWithChildren } from "react";

interface CardProps extends PropsWithChildren {
    title?: string;
    description?: string;
    className?: string;
}

export function Card({ children, title, description, className }: CardProps) {
    return (
        <section className={`card${className ? ` ${className}` : ""}`}>
            {title ? <h3 className="card-title">{title}</h3> : null}
            {description ? <p className="card-description">{description}</p> : null}
            {children}
        </section>
    );
}

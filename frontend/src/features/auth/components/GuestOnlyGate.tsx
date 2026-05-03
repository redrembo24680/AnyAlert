"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/features/auth/contexts/AuthContext";

interface GuestOnlyGateProps {
    children: ReactNode;
    redirectTo?: string;
}

export function GuestOnlyGate({ children, redirectTo = "/" }: GuestOnlyGateProps) {
    const { isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (isAuthenticated) {
            router.replace(redirectTo);
        }
    }, [isAuthenticated, redirectTo, router]);

    if (isAuthenticated) {
        return null;
    }

    return <>{children}</>;
}
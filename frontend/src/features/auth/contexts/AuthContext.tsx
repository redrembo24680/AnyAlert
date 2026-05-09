"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { AuthUser, AuthResponse } from "@/shared/types/api";

interface AuthContextType {
    user: AuthUser | null;
    isAuthenticated: boolean;
    login: (response: AuthResponse) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const SESSION_KEY = "anyalert:session";

function isTokenExpired(token: string): boolean {
    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        return typeof payload.exp === "number" && Date.now() / 1000 > payload.exp;
    } catch {
        return true;
    }
}

function isValidAuthResponse(value: unknown): value is AuthResponse {
    if (!value || typeof value !== "object") {
        return false;
    }

    const candidate = value as Partial<AuthResponse>;
    return (
        typeof candidate.token === "string" &&
        candidate.token.trim().length > 0 &&
        !!candidate.user &&
        typeof candidate.user.email === "string"
    );
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    // Restore session from localStorage on mount
    useEffect(() => {
        // Ensure this runs only on client side
        if (typeof window === "undefined") {
            return;
        }

        try {
            // Try to read from localStorage
            const stored = localStorage.getItem(SESSION_KEY);
            if (stored) {
                const parsed: unknown = JSON.parse(stored);
                if (isValidAuthResponse(parsed) && !isTokenExpired(parsed.token)) {
                    setUser(parsed.user);
                } else {
                    localStorage.removeItem(SESSION_KEY);
                }
            }
        } catch (e) {
            console.error("Failed to restore session from localStorage:", e);
            localStorage.removeItem(SESSION_KEY);
        } finally {
            // Mark as loaded after attempting to restore
            setIsLoaded(true);
        }
    }, []); // Empty dependency - run only once on mount

    const login = (response: AuthResponse) => {
        // Save to localStorage
        try {
            localStorage.setItem(SESSION_KEY, JSON.stringify(response));
        } catch (e) {
            console.error("Failed to save session to localStorage:", e);
        }
        // Update state
        setUser(response.user);
    };

    const logout = () => {
        try {
            localStorage.removeItem(SESSION_KEY);
        } catch (e) {
            console.error("Failed to clear session from localStorage:", e);
        }
        setUser(null);
    };

    // Don't render children until we've checked localStorage to prevent hydration mismatch
    if (!isLoaded) {
        return null;
    }

    return (
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

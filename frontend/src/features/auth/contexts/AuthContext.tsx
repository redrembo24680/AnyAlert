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

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem(SESSION_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored) as AuthResponse;
                setUser(parsed.user);
            } catch (e) {
                console.error("Failed to parse session", e);
            }
        }
        setIsLoaded(true);
    }, []);

    const login = (response: AuthResponse) => {
        localStorage.setItem(SESSION_KEY, JSON.stringify(response));
        setUser(response.user);
    };

    const logout = () => {
        localStorage.removeItem(SESSION_KEY);
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

import { useEffect } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";

/**
 * Хук для автоматичного відновлення сесії з localStorage
 * Це гарантує, що сесія не буде втрачена при гарячій перезагрузці
 */
export function useAuthPersist() {
    const { user, isAuthenticated } = useAuth();

    useEffect(() => {
        // Синхронізуємо стан коли сторінка повертається до фокусу
        const handleFocus = () => {
            // Сесія вже відновлена в AuthProvider на mount
            // Цей hook просто гарантує синхронізацію при повертанні
            if (typeof window !== "undefined" && window.localStorage) {
                const stored = localStorage.getItem("anyalert:session");
                if (stored && !user) {
                    // Якщо у localStorage є сесія, але user не завантажений
                    // Перезавантажимо сторінку щоб переінітіалізувати
                    window.location.reload();
                }
            }
        };

        window.addEventListener("focus", handleFocus);
        return () => window.removeEventListener("focus", handleFocus);
    }, [user]);

    return { user, isAuthenticated };
}

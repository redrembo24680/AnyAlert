import type { AuthResponse, LoginPayload, RegisterPayload } from "@/shared/types/api";

interface StoredUser {
    name: string;
    email: string;
    password: string;
}

const USERS_KEY = "anyalert:users";
const SESSION_KEY = "anyalert:session";

function wait(ms: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

function readUsers(): StoredUser[] {
    if (typeof window === "undefined") {
        return [];
    }

    const raw = window.localStorage.getItem(USERS_KEY);
    if (!raw) {
        return [];
    }

    try {
        const parsed = JSON.parse(raw) as StoredUser[];
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function writeUsers(users: StoredUser[]): void {
    if (typeof window === "undefined") {
        return;
    }

    window.localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function saveSession(response: AuthResponse): void {
    if (typeof window === "undefined") {
        return;
    }

    window.localStorage.setItem(SESSION_KEY, JSON.stringify(response));
}

export async function mockLogin(payload: LoginPayload): Promise<AuthResponse> {
    await wait(500);

    const users = readUsers();
    const user = users.find(
        (storedUser) =>
            storedUser.email.toLowerCase() === payload.email.toLowerCase() &&
            storedUser.password === payload.password
    );

    if (!user) {
        throw new Error("Невірний email або пароль");
    }

    const response: AuthResponse = {
        token: `mock-token-${Date.now()}`,
        user: {
            name: user.name,
            email: user.email
        }
    };

    saveSession(response);
    return response;
}

export async function mockRegister(payload: RegisterPayload): Promise<AuthResponse> {
    await wait(650);

    const users = readUsers();
    const alreadyExists = users.some(
        (storedUser) => storedUser.email.toLowerCase() === payload.email.toLowerCase()
    );

    if (alreadyExists) {
        throw new Error("Користувач з таким email вже існує");
    }

    users.push({
        name: payload.name,
        email: payload.email,
        password: payload.password
    });

    writeUsers(users);

    const response: AuthResponse = {
        token: `mock-token-${Date.now()}`,
        user: {
            name: payload.name,
            email: payload.email
        }
    };

    saveSession(response);
    return response;
}

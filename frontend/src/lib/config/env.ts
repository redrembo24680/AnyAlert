const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    (process.env.NODE_ENV !== "production" ? "http://localhost:8000/api/v1" : undefined);

if (!apiUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
}

export const env = {
    apiUrl
};

import type { TrackerCreatePayload, TrackerResponse } from "@/shared/types/api";
import { apiFetch } from "@/lib/api/http";

export async function createTracker(payload: TrackerCreatePayload, token: string): Promise<TrackerResponse> {
    return apiFetch<TrackerResponse>("/trackers/", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });
}

export async function getMyTrackers(token: string): Promise<TrackerResponse[]> {
    return apiFetch<TrackerResponse[]>("/trackers/", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
}

import { env } from "@/lib/config/env";

export async function deleteTracker(trackerId: number, token: string): Promise<void> {
    const response = await fetch(`${env.apiUrl}/trackers/${trackerId}`, {
        method: "DELETE",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
    if (!response.ok) {
        throw new Error("Failed to delete tracker");
    }
}




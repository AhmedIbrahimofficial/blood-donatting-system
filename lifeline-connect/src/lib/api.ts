/**
 * Thin API client for the Blood Donor Matching backend.
 *
 * Dev mein Vite proxy /api/* → http://localhost:8000 handle karta hai.
 * Production mein VITE_API_BASE_URL set karo.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

// ---------------------------------------------------------------------------
// Shared fetch helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof localStorage !== "undefined" ? localStorage.getItem("access_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail: unknown;
    try { detail = await response.json(); } catch { detail = response.statusText; }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

// Multipart form upload (no Content-Type header — browser sets boundary)
async function apiFetchForm<T>(path: string, form: FormData): Promise<T> {
  const token =
    typeof localStorage !== "undefined" ? localStorage.getItem("access_token") : null;

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!response.ok) {
    let detail: unknown;
    try { detail = await response.json(); } catch { detail = response.statusText; }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: unknown,
  ) {
    super(`API error ${status}`);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface TokenResponse { access_token: string; token_type: string; }

export async function googleLogin(id_token: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token }),
  });
}

// ---------------------------------------------------------------------------
// Donor profile
// ---------------------------------------------------------------------------

export type VerificationStatus = "pending" | "verified" | "rejected";

export interface DonorProfile {
  id: number;
  user_id: number;
  blood_type: string;
  latitude: number;
  longitude: number;
  is_available: boolean;
  verification_status: VerificationStatus;
  last_donation_date: string | null;
  next_eligible_date: string | null;
}

export async function getMyProfile(): Promise<DonorProfile> {
  return apiFetch<DonorProfile>("/api/v1/donors/profile");
}

export async function upsertProfile(data: {
  blood_type: string;
  latitude: number;
  longitude: number;
}): Promise<DonorProfile> {
  const form = new FormData();
  form.append("blood_type", data.blood_type);
  form.append("latitude", String(data.latitude));
  form.append("longitude", String(data.longitude));
  return apiFetchForm<DonorProfile>("/api/v1/donors/profile", form);
}

export async function updateAvailability(is_available: boolean): Promise<DonorProfile> {
  return apiFetch<DonorProfile>("/api/v1/donors/availability", {
    method: "PATCH",
    body: JSON.stringify({ is_available }),
  });
}

export interface DonationHistoryItem {
  id: number;
  date: string;
  hospital_name: string;
  units: number;
}

export async function getDonationHistory(user_id: number): Promise<DonationHistoryItem[]> {
  return apiFetch<DonationHistoryItem[]>(`/api/v1/donors/${user_id}/history`);
}

// ---------------------------------------------------------------------------
// Blood banks
// ---------------------------------------------------------------------------

export interface BloodBank {
  id: number;
  name: string;
  phone: string;
  latitude: number;
  longitude: number;
  verified: boolean;
  distance_km: number;
}

export async function fetchNearbyBloodBanks(params: {
  lat: number;
  lng: number;
  radius_km?: number;
}): Promise<BloodBank[]> {
  const { lat, lng, radius_km = 20 } = params;
  const qs = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius_km: String(radius_km),
  });
  return apiFetch<BloodBank[]>(`/api/v1/blood-banks/nearby?${qs}`);
}

// ---------------------------------------------------------------------------
// Emergency requests
// ---------------------------------------------------------------------------

export type UrgencyLevel = "critical" | "urgent" | "planned";
export type RequestStatus = "open" | "matched" | "fulfilled" | "expired";

export interface EmergencyRequestPayload {
  blood_type_needed: string;
  units_needed: number;
  hospital_name: string;
  latitude: number;
  longitude: number;
  urgency_level: UrgencyLevel;
  radius_km?: number;
}

export interface EmergencyRequestAccepted {
  id: number;
  status: RequestStatus;
  message: string;
}

export async function createEmergencyRequest(
  body: EmergencyRequestPayload,
): Promise<EmergencyRequestAccepted> {
  return apiFetch<EmergencyRequestAccepted>("/api/v1/requests/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * Centralized error handling utilities for API calls.
 */
import { ApiError } from "./api";
import { toast } from "sonner";

/**
 * Handle an API error and show an appropriate toast message.
 * Returns a human-readable error message.
 */
export function handleApiError(err: unknown, fallback = "Something went wrong."): string {
  if (err instanceof ApiError) {
    const detail = err.detail as { message?: string; code?: string } | string | null;

    // Rate limit
    if (err.status === 429) {
      toast.error("Too many requests. Please slow down.");
      return "Rate limit exceeded.";
    }

    // Unauthorized
    if (err.status === 401) {
      toast.error("Session expired. Please log in again.");
      return "Unauthorized.";
    }

    // Server error
    if (err.status >= 500) {
      toast.error("Server error. Our team has been notified.");
      return "Server error.";
    }

    // Validation error
    if (err.status === 422) {
      const msg =
        typeof detail === "object" && detail !== null && "message" in detail
          ? detail.message
          : "Validation failed. Check your inputs.";
      toast.error(msg ?? fallback);
      return msg ?? fallback;
    }

    // Other 4xx
    const msg =
      typeof detail === "string"
        ? detail
        : typeof detail === "object" && detail?.message
          ? detail.message
          : fallback;

    toast.error(msg);
    return msg;
  }

  // Network error
  if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
    toast.error("Cannot reach the server. Check your connection.");
    return "Network error.";
  }

  toast.error(fallback);
  return fallback;
}

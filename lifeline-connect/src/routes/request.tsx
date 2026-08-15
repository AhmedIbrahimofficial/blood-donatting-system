import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertTriangle, CalendarClock, Siren } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/site/PageHeader";
import { createEmergencyRequest, ApiError, type UrgencyLevel } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/request")({
  head: () => ({
    meta: [
      { title: "Request Blood Urgently — LifeLink" },
      {
        name: "description",
        content:
          "Send an emergency blood request to matching donors near your hospital in seconds.",
      },
      { property: "og:title", content: "Request Blood Urgently — LifeLink" },
      { property: "og:description", content: "Alert nearby matching donors in seconds." },
    ],
  }),
  component: RequestPage,
});

const bloodTypes = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

const urgencies: Array<{
  id: UrgencyLevel;
  label: string;
  note: string;
  icon: React.ElementType;
  tone: string;
}> = [
  { id: "critical", label: "Critical", note: "Needed within 2 hours", icon: Siren, tone: "critical" },
  { id: "urgent", label: "Urgent", note: "Needed today", icon: AlertTriangle, tone: "urgent" },
  { id: "planned", label: "Planned", note: "Scheduled procedure", icon: CalendarClock, tone: "planned" },
];

// Browser geolocation — Lahore centre as fallback
async function getLocation(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: 31.5204, lng: 74.3587 });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve({ lat: 31.5204, lng: 74.3587 }),
      { timeout: 5000 },
    );
  });
}

function RequestPage() {
  const navigate = useNavigate();
  const { isLoggedIn } = useAuth();

  const [bloodType, setBloodType] = useState<string | null>(null);
  const [urgency, setUrgency] = useState<UrgencyLevel>("critical");
  const [loading, setLoading] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (!bloodType) {
      toast.error("Select the blood type needed");
      return;
    }

    if (!isLoggedIn) {
      toast.error("You must be logged in to send a request", {
        description: "Sign in to your donor account first.",
        action: { label: "Login", onClick: () => navigate({ to: "/login" }) },
      });
      return;
    }

    const form = e.currentTarget;
    const units = parseInt((form.elements.namedItem("units") as HTMLInputElement).value, 10);
    const hospital = (form.elements.namedItem("hospital") as HTMLInputElement).value.trim();

    if (!hospital) {
      setFieldError("Enter the hospital name and location.");
      return;
    }
    setFieldError(null);
    setLoading(true);

    try {
      // Get real browser location
      const { lat, lng } = await getLocation();

      const response = await createEmergencyRequest({
        blood_type_needed: bloodType,
        units_needed: units,
        hospital_name: hospital,
        latitude: lat,
        longitude: lng,
        urgency_level: urgency,
        radius_km: 25,
      });

      toast.success("Emergency alert sent", {
        description: `Request #${response.id} accepted. Matching donors are being notified.`,
      });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        toast.error("Session expired — please log in again.");
        navigate({ to: "/login" });
      } else {
        toast.error("Could not send request. Check your connection or try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Emergency request"
        title="Request blood now"
        description="Fill this in once — every compatible, available donor near the hospital is alerted immediately."
      />

      <section className="section-y">
        <form className="mx-auto max-w-2xl px-5" onSubmit={handleSubmit}>
          <div className="rounded-xl border border-border bg-card p-8 shadow-[var(--shadow-card)]">
            <h2 className="text-lg font-bold text-ink">Blood type needed</h2>
            <div className="mt-4 grid grid-cols-4 gap-3">
              {bloodTypes.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setBloodType(t)}
                  className={`rounded-[10px] border px-3 py-3.5 text-base font-extrabold transition-colors ${
                    bloodType === t
                      ? "border-primary bg-primary text-primary-foreground shadow-[var(--shadow-btn)]"
                      : "border-border bg-accent/50 text-ink hover:border-primary"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="mt-8 grid gap-5 sm:grid-cols-2">
              <div>
                <label htmlFor="units" className="text-sm font-semibold text-ink">
                  Units needed
                </label>
                <input
                  id="units"
                  name="units"
                  type="number"
                  min={1}
                  max={20}
                  defaultValue={1}
                  className="mt-2 w-full rounded-[10px] border border-input bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
                />
              </div>
              <div>
                <label htmlFor="hospital" className="text-sm font-semibold text-ink">
                  Hospital name and location
                </label>
                <input
                  id="hospital"
                  name="hospital"
                  maxLength={200}
                  placeholder="e.g. Services Hospital, Jail Road, Lahore"
                  className="mt-2 w-full rounded-[10px] border border-input bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
                />
              </div>
            </div>

            {fieldError && (
              <p className="mt-3 text-xs text-destructive">{fieldError}</p>
            )}

            <h2 className="mt-8 text-lg font-bold text-ink">Urgency level</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {urgencies.map((u) => {
                const active = urgency === u.id;
                return (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => setUrgency(u.id)}
                    className={`rounded-[10px] border p-4 text-left transition-colors ${
                      active
                        ? "border-transparent shadow-[var(--shadow-card)]"
                        : "border-border bg-card hover:border-primary"
                    }`}
                    style={
                      active
                        ? {
                            backgroundColor: `var(--${u.tone})`,
                            color: "var(--primary-foreground)",
                          }
                        : undefined
                    }
                  >
                    <u.icon className="size-5" aria-hidden="true" />
                    <p className="mt-3 text-sm font-bold">{u.label}</p>
                    <p className={`mt-1 text-xs ${active ? "opacity-90" : "text-muted-foreground"}`}>
                      {u.note}
                    </p>
                  </button>
                );
              })}
            </div>

            {!isLoggedIn && (
              <p className="mt-6 rounded-[10px] border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
                You need to be logged in to send a request. Your form data will be preserved.
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-8 w-full rounded-[10px] bg-primary px-6 py-4 text-base font-extrabold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark disabled:opacity-60"
            >
              {loading ? "Sending alert…" : "Send emergency alert"}
            </button>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              For life-threatening emergencies also call the helpline: 1122
            </p>
          </div>
        </form>
      </section>
    </>
  );
}

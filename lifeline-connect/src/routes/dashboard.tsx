import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Droplet, History, Loader2, Settings, User } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { PageHeader } from "@/components/site/PageHeader";
import {
  getMyProfile,
  upsertProfile,
  updateAvailability,
  getDonationHistory,
  ApiError,
  type DonorProfile,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Donor Dashboard — LifeLink" },
      { name: "description", content: "Manage your donor profile, availability and donation history." },
    ],
  }),
  component: DashboardPage,
});

const tabs = [
  { id: "profile", label: "Profile", icon: User },
  { id: "availability", label: "Availability", icon: Droplet },
  { id: "history", label: "Donation history", icon: History },
  { id: "settings", label: "Settings", icon: Settings },
] as const;

const BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

// Default location — Lahore centre (used when browser denies geolocation)
const DEFAULT_LAT = 31.5204;
const DEFAULT_LNG = 74.3587;

function DashboardPage() {
  const navigate = useNavigate();
  const { isLoggedIn } = useAuth();
  const qc = useQueryClient();

  const [tab, setTab] = useState<string>("profile");

  // ── Redirect if not logged in ────────────────────────────────────────────
  if (!isLoggedIn) {
    return (
      <section className="section-y">
        <div className="mx-auto max-w-md px-5 text-center">
          <h2 className="text-xl font-bold text-ink">You are not logged in</h2>
          <p className="mt-2 text-sm text-muted-foreground">Sign in to access your dashboard.</p>
          <button
            onClick={() => navigate({ to: "/login" })}
            className="mt-6 rounded-[10px] bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
          >
            Go to Login
          </button>
        </div>
      </section>
    );
  }

  return <DashboardContent tab={tab} setTab={setTab} />;
}

// ── Main dashboard (only rendered when logged in) ────────────────────────────
function DashboardContent({
  tab,
  setTab,
}: {
  tab: string;
  setTab: (t: string) => void;
}) {
  const qc = useQueryClient();

  // Fetch profile
  const {
    data: profile,
    isLoading: profileLoading,
    isError: profileError,
  } = useQuery<DonorProfile, ApiError>({
    queryKey: ["my-profile"],
    queryFn: getMyProfile,
    retry: false,
  });

  // Fetch donation history (only when profile loaded)
  const { data: history = [] } = useQuery({
    queryKey: ["my-history", profile?.user_id],
    queryFn: () => getDonationHistory(profile!.user_id),
    enabled: !!profile,
  });

  // Availability toggle mutation
  const availMutation = useMutation({
    mutationFn: (val: boolean) => updateAvailability(val),
    onSuccess: (updated) => {
      qc.setQueryData(["my-profile"], updated);
      toast.success(updated.is_available ? "You are now available" : "Availability paused");
    },
    onError: (err: ApiError) => {
      const detail = err.detail as { message?: string } | null;
      toast.error(detail?.message ?? "Could not update availability");
    },
  });

  // Profile upsert state
  const [bloodType, setBloodType] = useState<string>("");
  const [saving, setSaving] = useState(false);

  async function handleSaveProfile() {
    if (!bloodType) { toast.error("Select a blood type"); return; }
    setSaving(true);
    try {
      // Get browser location if available, else default
      const { lat, lng } = await getBrowserLocation();
      const updated = await upsertProfile({ blood_type: bloodType, latitude: lat, longitude: lng });
      qc.setQueryData(["my-profile"], updated);
      toast.success("Profile saved!");
    } catch {
      toast.error("Could not save profile");
    } finally {
      setSaving(false);
    }
  }

  const headerDesc = profile
    ? `Blood type ${profile.blood_type} · ${profile.verification_status === "verified" ? "Verified donor" : "Pending verification"}`
    : "Loading your profile…";

  return (
    <>
      <PageHeader eyebrow="Dashboard" title="Welcome back" description={headerDesc} />

      <section className="section-y">
        <div className="mx-auto grid max-w-6xl gap-8 px-5 lg:grid-cols-[240px_1fr]">
          {/* Sidebar nav */}
          <nav className="h-fit rounded-xl border border-border bg-card p-2 shadow-[var(--shadow-card)]">
            <ul className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
              {tabs.map((t) => (
                <li key={t.id} className="flex-1">
                  <button
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`flex w-full items-center gap-2 whitespace-nowrap rounded-[10px] px-3 py-2.5 text-sm font-semibold transition-colors ${
                      tab === t.id
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-secondary"
                    }`}
                  >
                    <t.icon className="size-4" />
                    {t.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Content */}
          <div className="rounded-xl border border-border bg-card p-8 shadow-[var(--shadow-card)]">

            {/* Loading */}
            {profileLoading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="size-8 animate-spin text-primary" />
              </div>
            )}

            {/* ── Profile tab ── */}
            {!profileLoading && tab === "profile" && (
              <div>
                <h2 className="text-xl font-bold text-ink">Profile</h2>

                {profile ? (
                  <dl className="mt-6 grid gap-5 sm:grid-cols-2">
                    {[
                      ["Blood type", profile.blood_type],
                      ["Status", profile.verification_status],
                      ["Last donation", profile.last_donation_date ?? "—"],
                      ["Eligible again", profile.next_eligible_date ?? "—"],
                    ].map(([k, v]) => (
                      <div key={k} className="rounded-[10px] border border-border bg-secondary/50 p-4">
                        <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{k}</dt>
                        <dd className="mt-1 text-sm font-bold text-ink capitalize">{v}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-4 text-sm text-muted-foreground">No profile yet. Set it up below.</p>
                )}

                {/* Set / update profile form */}
                <div className="mt-8 rounded-[10px] border border-border bg-secondary/50 p-5">
                  <h3 className="text-sm font-bold text-ink">
                    {profile ? "Update blood type" : "Set up your profile"}
                  </h3>
                  <div className="mt-4 grid grid-cols-4 gap-2">
                    {BLOOD_TYPES.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setBloodType(t)}
                        className={`rounded-[10px] border py-2.5 text-sm font-extrabold transition-colors ${
                          bloodType === t || (!bloodType && profile?.blood_type === t)
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border bg-background text-ink hover:border-primary"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={handleSaveProfile}
                    className="mt-4 rounded-[10px] bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-60"
                  >
                    {saving ? "Saving…" : "Save profile"}
                  </button>
                </div>
              </div>
            )}

            {/* ── Availability tab ── */}
            {!profileLoading && tab === "availability" && (
              <div>
                <h2 className="text-xl font-bold text-ink">Availability</h2>
                {!profile ? (
                  <p className="mt-4 text-sm text-muted-foreground">
                    Create your profile first to manage availability.
                  </p>
                ) : (
                  <>
                    <div className="mt-6 flex items-center justify-between rounded-[10px] border border-border bg-secondary/50 p-5">
                      <div>
                        <p className="text-sm font-bold text-ink">
                          {profile.is_available ? "Available for requests" : "Paused"}
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {profile.is_available
                            ? "You will receive alerts for matching requests near you."
                            : "You will not be alerted until you turn this back on."}
                        </p>
                      </div>
                      <Switch
                        checked={profile.is_available}
                        disabled={availMutation.isPending}
                        onCheckedChange={(val) => availMutation.mutate(val)}
                        aria-label="Toggle availability"
                      />
                    </div>
                    <p className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                      <Bell className="size-4 text-primary" />
                      Alerts pause automatically for 56 days after each whole-blood donation.
                    </p>
                  </>
                )}
              </div>
            )}

            {/* ── Donation history tab ── */}
            {!profileLoading && tab === "history" && (
              <div>
                <h2 className="text-xl font-bold text-ink">Donation history</h2>
                {history.length === 0 ? (
                  <p className="mt-6 text-sm text-muted-foreground">No donations recorded yet.</p>
                ) : (
                  <div className="mt-6 divide-y divide-border overflow-hidden rounded-[10px] border border-border">
                    {history.map((h) => (
                      <div key={h.id} className="flex items-center justify-between gap-4 p-4">
                        <div>
                          <p className="text-sm font-bold text-ink">{h.hospital_name}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{h.date}</p>
                        </div>
                        <span className="rounded-md bg-accent px-2.5 py-1 text-xs font-bold text-accent-foreground">
                          {h.units} unit{h.units > 1 ? "s" : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── Settings tab ── */}
            {!profileLoading && tab === "settings" && (
              <div>
                <h2 className="text-xl font-bold text-ink">Settings</h2>
                <p className="mt-4 text-sm text-muted-foreground">
                  Notification settings coming soon.
                </p>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

// ── Browser geolocation helper ───────────────────────────────────────────────
function getBrowserLocation(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: DEFAULT_LAT, lng: DEFAULT_LNG });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve({ lat: DEFAULT_LAT, lng: DEFAULT_LNG }),
      { timeout: 5000 },
    );
  });
}

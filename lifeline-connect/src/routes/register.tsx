import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Check, MapPin } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/site/PageHeader";
import { signInWithGoogle } from "@/lib/firebase";
import { googleLogin, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Become a Donor — LifeLink Registration" },
      {
        name: "description",
        content: "Register as a blood donor in three steps: Google sign-in, blood type, and location.",
      },
      { property: "og:title", content: "Become a Donor — LifeLink Registration" },
      { property: "og:description", content: "Join the verified LifeLink donor registry." },
    ],
  }),
  component: RegisterPage,
});

const bloodTypes = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
const stepLabels = ["Sign in", "Blood type", "Location", "Done"];

function RegisterPage() {
  const navigate = useNavigate();
  const { setToken, isLoggedIn } = useAuth();

  const [step, setStep] = useState(isLoggedIn ? 1 : 0);
  const [bloodType, setBloodType] = useState<string | null>(null);
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);

  // ── Step 0: Google Sign-In ───────────────────────────────────────────────
  async function handleGoogleSignIn() {
    setLoading(true);
    try {
      const credential = await signInWithGoogle();
      const idToken = await credential.user.getIdToken();
      const { access_token } = await googleLogin(idToken);
      setToken(access_token);
      toast.success(`Welcome, ${credential.user.displayName ?? "Donor"}!`);
      setStep(1);
    } catch (err) {
      if ((err as { code?: string })?.code === "auth/popup-closed-by-user") return;
      if (err instanceof ApiError) toast.error("Sign-in failed. Try again.");
      else toast.error("Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }

  function handleNext() {
    if (step === 1 && !bloodType) {
      toast.error("Select your blood type to continue");
      return;
    }
    if (step < stepLabels.length - 1) setStep((s) => s + 1);
  }

  return (
    <>
      <PageHeader
        eyebrow="Become a donor"
        title="Register in three short steps"
        description="It takes about two minutes. We only share your contact details with a patient after you accept a request."
      />

      <section className="section-y">
        <div className="mx-auto max-w-3xl px-5">
          {/* Progress indicator */}
          <ol className="flex items-center">
            {stepLabels.map((label, i) => (
              <li key={label} className="flex flex-1 items-center last:flex-none">
                <div className="flex flex-col items-center gap-2">
                  <span
                    className={`flex size-10 items-center justify-center rounded-full border-2 text-sm font-bold transition-colors ${
                      i < step
                        ? "border-primary bg-primary text-primary-foreground"
                        : i === step
                          ? "border-primary bg-background text-primary"
                          : "border-border bg-background text-muted-foreground"
                    }`}
                  >
                    {i < step ? <Check className="size-5" /> : i + 1}
                  </span>
                  <span className="hidden text-xs font-semibold text-muted-foreground sm:block">
                    {label}
                  </span>
                </div>
                {i < stepLabels.length - 1 && (
                  <span className={`mx-2 mb-6 h-0.5 flex-1 ${i < step ? "bg-primary" : "bg-border"}`} />
                )}
              </li>
            ))}
          </ol>

          <div className="mt-10 rounded-xl border border-border bg-card p-8 shadow-[var(--shadow-card)]">

            {/* ── Step 0: Google Sign-In ── */}
            {step === 0 && (
              <div className="text-center">
                <h2 className="text-2xl font-extrabold text-ink">Create your account</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Sign in with Google to get started. No password needed.
                </p>
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={loading}
                  className="mx-auto mt-8 flex items-center justify-center gap-3 rounded-[10px] border border-border bg-card px-6 py-3 text-sm font-semibold text-ink shadow-[var(--shadow-card)] transition-colors hover:bg-secondary disabled:opacity-60"
                >
                  <svg className="size-5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                  {loading ? "Signing in…" : "Continue with Google"}
                </button>
                <p className="mt-6 text-sm text-muted-foreground">
                  Already a donor?{" "}
                  <Link to="/login" className="font-semibold text-primary">Sign in</Link>
                </p>
              </div>
            )}

            {/* ── Step 1: Blood type ── */}
            {step === 1 && (
              <div>
                <h2 className="text-2xl font-extrabold text-ink">What is your blood type?</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Pick the group printed on your donor card or last lab report.
                </p>
                <div className="mt-7 grid grid-cols-4 gap-3">
                  {bloodTypes.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setBloodType(t)}
                      className={`rounded-[10px] border px-3 py-4 text-lg font-extrabold transition-colors ${
                        bloodType === t
                          ? "border-primary bg-primary text-primary-foreground shadow-[var(--shadow-btn)]"
                          : "border-border bg-accent/50 text-ink hover:border-primary"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ── Step 2: Location ── */}
            {step === 2 && (
              <div>
                <h2 className="text-2xl font-extrabold text-ink">Where are you based?</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  We match requests within roughly 25 km of your area.
                </p>
                <label htmlFor="address" className="mt-7 block text-sm font-semibold text-ink">
                  Address or area
                </label>
                <div className="mt-2 flex items-center gap-2 rounded-[10px] border border-input bg-background px-3">
                  <MapPin className="size-4 text-primary" aria-hidden="true" />
                  <input
                    id="address"
                    maxLength={160}
                    placeholder="e.g. Gulberg III, Lahore"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full bg-transparent py-2.5 text-sm outline-none"
                  />
                </div>
                <div className="mt-5 flex h-48 items-center justify-center rounded-[10px] border border-dashed border-border bg-secondary/70 text-sm text-muted-foreground">
                  Map preview — pin drops on your saved area
                </div>
              </div>
            )}

            {/* ── Step 3: Done ── */}
            {step === 3 && (
              <div className="text-center">
                <span className="mx-auto flex size-16 items-center justify-center rounded-full bg-primary/10">
                  <Check className="size-8 text-primary" />
                </span>
                <h2 className="mt-5 text-2xl font-extrabold text-ink">You're registered!</h2>
                <p className="mt-3 text-sm text-muted-foreground">
                  Your account is active. ID verification completes within 24 hours.
                </p>
                <Link
                  to="/dashboard"
                  className="mt-8 inline-flex rounded-[10px] bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
                >
                  Go to your dashboard
                </Link>
              </div>
            )}

            {/* Nav buttons */}
            {step > 0 && step < 3 && (
              <div className="mt-8 flex items-center justify-between gap-3 border-t border-border pt-6">
                <button
                  type="button"
                  onClick={() => setStep((s) => Math.max(1, s - 1))}
                  className="rounded-[10px] border border-border px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-secondary"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleNext}
                  className="rounded-[10px] bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
                >
                  {step === 2 ? "Finish registration" : "Next"}
                </button>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

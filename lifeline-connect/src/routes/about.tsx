import { createFileRoute, Link } from "@tanstack/react-router";
import { HeartHandshake, Search, UserPlus } from "lucide-react";
import heroImage from "@/assets/hero-donation.jpg";
import { PageHeader } from "@/components/site/PageHeader";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About LifeLink — How Donor Matching Works" },
      {
        name: "description",
        content:
          "Our mission, the three-step matching process, and the team keeping LifeLink's donor network verified and ready.",
      },
      { property: "og:title", content: "About LifeLink — How Donor Matching Works" },
      {
        property: "og:description",
        content: "Register, get matched, save a life — how LifeLink works.",
      },
    ],
  }),
  component: AboutPage,
});

const steps = [
  {
    icon: UserPlus,
    title: "Register",
    body: "Create a donor profile with your blood type, city and availability. Verification takes under a day.",
  },
  {
    icon: Search,
    title: "Get matched",
    body: "When a compatible request appears near you, we alert you instantly with hospital and urgency details.",
  },
  {
    icon: HeartHandshake,
    title: "Save a life",
    body: "Accept, donate at the listed hospital or blood bank, and log the donation to your history.",
  },
];

function AboutPage() {
  return (
    <>
      <PageHeader
        eyebrow="About us"
        title="A donor network built for the first critical hour"
        description="Most blood emergencies are lost to time, not scarcity. LifeLink keeps a verified, geo-aware donor registry so hospitals and families reach the right person on the first call."
      />

      <section className="section-y">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-extrabold text-ink md:text-4xl">Our mission</h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground">
              LifeLink exists to remove the frantic phone-tree that follows every emergency
              transfusion request. We maintain a registry of screened donors, match them by blood
              group compatibility and travel distance, and hand the family a shortlist instead of a
              rumour.
            </p>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground">
              We work alongside public hospitals, licensed blood banks and campus donor societies.
              Every donor is contactable only through the platform until they accept a request, so
              privacy stays intact.
            </p>
            <Link
              to="/register"
              className="mt-8 inline-flex rounded-[10px] bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
            >
              Join the donor registry
            </Link>
          </div>
          <img
            src={heroImage}
            alt="A nurse assisting a donor during a blood donation"
            loading="lazy"
            width={1920}
            height={1088}
            className="h-80 w-full rounded-xl object-cover shadow-[var(--shadow-card)]"
          />
        </div>
      </section>

      <section className="section-y bg-secondary/50">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="text-3xl font-extrabold text-ink md:text-4xl">How it works</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {steps.map((s, i) => (
              <div
                key={s.title}
                className="rounded-xl border border-border bg-card p-7 shadow-[var(--shadow-card)]"
              >
                <span className="flex size-12 items-center justify-center rounded-[10px] bg-accent text-accent-foreground">
                  <s.icon className="size-6" />
                </span>
                <p className="mt-6 text-xs font-bold uppercase tracking-[0.18em] text-primary">
                  Step {i + 1}
                </p>
                <h3 className="mt-2 text-xl font-bold text-ink">{s.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-y">
        <div className="mx-auto max-w-3xl px-5 text-center">
          <h2 className="text-3xl font-extrabold text-ink md:text-4xl">Who runs LifeLink</h2>
          <p className="mt-5 text-base leading-relaxed text-muted-foreground">
            LifeLink is operated by a small non-profit team of transfusion-medicine volunteers,
            hospital coordinators and engineers. Our medical advisory board reviews every screening
            rule, and the platform is funded by grants — never by charging donors or patients.
          </p>
        </div>
      </section>
    </>
  );
}
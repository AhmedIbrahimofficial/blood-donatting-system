import { createFileRoute, Link } from "@tanstack/react-router";
import { HeartHandshake, Quote, Search, UserPlus } from "lucide-react";
import heroImage from "@/assets/hero-donation.jpg";
import testimonialImage from "@/assets/testimonial.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LifeLink — Find a Blood Donor Near You in Minutes" },
      {
        name: "description",
        content:
          "LifeLink matches verified blood donors with patients in emergencies by blood type and distance. Register as a donor or send an urgent request.",
      },
      { property: "og:title", content: "LifeLink — Find a Blood Donor Near You in Minutes" },
      {
        property: "og:description",
        content: "Verified donors, matched by blood type and distance, alerted instantly.",
      },
    ],
  }),
  component: Index,
});

const steps = [
  {
    icon: UserPlus,
    title: "Register",
    body: "Add your blood type, area and availability. Verification is manual and takes under a day.",
  },
  {
    icon: Search,
    title: "Get matched",
    body: "We alert compatible donors within 25 km of the hospital the moment a request is filed.",
  },
  {
    icon: HeartHandshake,
    title: "Save a life",
    body: "Accept, donate at the listed centre, and your donation is logged to your history.",
  },
];

const stats = [
  { value: "42,800", label: "Donors registered" },
  { value: "11,300", label: "Lives helped" },
  { value: "18 min", label: "Median match time" },
  { value: "260", label: "Partner hospitals" },
];

function Index() {
  return (
    <>
      <section className="relative isolate min-h-[560px] overflow-hidden md:min-h-[640px]">
        <img
          src={heroImage}
          alt="A nurse assisting a smiling donor giving blood at a clinic"
          width={1920}
          height={1088}
          className="absolute inset-0 -z-20 size-full object-cover"
        />
        <div className="hero-overlay absolute inset-0 -z-10" />
        <div className="mx-auto flex min-h-[560px] max-w-6xl flex-col justify-center px-5 py-24 md:min-h-[640px]">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary-foreground/80">
              Emergency donor matching
            </p>
            <h1 className="mt-4 text-4xl font-extrabold leading-tight text-primary-foreground md:text-6xl">
              Someone nearby needs your help
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-primary-foreground/90 md:text-lg">
              Join a community of donors saving lives, one match at a time. LifeLink finds the right
              blood type, in the right place, at the right hour.
            </p>
            <div className="mt-9 flex flex-wrap gap-4">
              <Link
                to="/register"
                className="rounded-[10px] bg-primary px-7 py-3.5 text-sm font-bold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
              >
                I want to help
              </Link>
              <Link
                to="/request"
                className="rounded-[10px] border border-primary-foreground/40 bg-background/95 px-7 py-3.5 text-sm font-bold text-primary transition-colors hover:bg-background"
              >
                I need blood urgently
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section-y">
        <div className="mx-auto max-w-6xl px-5">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">How it works</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-extrabold text-ink md:text-4xl">
            Three steps between a request and a transfusion
          </h2>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((s, i) => (
              <div
                key={s.title}
                className="rounded-xl border border-border bg-card p-7 shadow-[var(--shadow-card)]"
              >
                <span className="flex size-12 items-center justify-center rounded-[10px] bg-primary text-primary-foreground shadow-[var(--shadow-btn)]">
                  <s.icon className="size-6" />
                </span>
                <p className="mt-6 text-xs font-bold uppercase tracking-[0.18em] text-muted-foreground">
                  Step {i + 1}
                </p>
                <h3 className="mt-2 text-xl font-bold text-ink">{s.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-y bg-secondary/60">
        <div className="mx-auto max-w-6xl px-5">
          <h2 className="text-3xl font-extrabold text-ink md:text-4xl">Trusted where it counts</h2>
          <p className="mt-3 max-w-xl text-base text-muted-foreground">
            Numbers from our partner hospital network over the last twelve months.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((s) => (
              <div
                key={s.label}
                className="rounded-xl border border-border bg-card p-7 shadow-[var(--shadow-card)]"
              >
                <p className="font-display text-4xl font-extrabold text-primary">{s.value}</p>
                <p className="mt-2 text-sm font-medium text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-y">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 md:grid-cols-[320px_1fr]">
          <img
            src={testimonialImage}
            alt="Nasreen Bibi, whose surgery was supported by LifeLink donors"
            loading="lazy"
            width={800}
            height={800}
            className="h-80 w-full rounded-xl object-cover shadow-[var(--shadow-card)]"
          />
          <figure>
            <Quote className="size-8 text-primary" />
            <blockquote className="mt-5 text-xl leading-relaxed text-ink md:text-2xl">
              “My mother needed three units of O− at two in the morning. We had called every relative
              we knew. LifeLink found two donors within nine minutes, and both were at the hospital
              before dawn.”
            </blockquote>
            <figcaption className="mt-6 text-sm font-semibold text-muted-foreground">
              Nasreen Bibi · Lahore
            </figcaption>
            <Link
              to="/register"
              className="mt-8 inline-flex rounded-[10px] bg-primary px-6 py-3 text-sm font-bold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
            >
              Become a donor
            </Link>
          </figure>
        </div>
      </section>
    </>
  );
}

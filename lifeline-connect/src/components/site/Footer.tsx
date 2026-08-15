import { Link } from "@tanstack/react-router";
import { Droplet, Facebook, Instagram, Mail, MapPin, Phone, Twitter } from "lucide-react";

const quickLinks = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/request", label: "Request Blood" },
  { to: "/register", label: "Become a Donor" },
  { to: "/blood-banks", label: "Blood Banks" },
  { to: "/dashboard", label: "Donor Dashboard" },
] as const;

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-secondary/60">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-4">
        <div className="md:col-span-1">
          <div className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary">
              <Droplet className="size-4 text-primary-foreground" fill="currentColor" />
            </span>
            <span className="font-display text-base font-extrabold text-ink">LifeLink</span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            LifeLink connects verified blood donors with patients in emergencies — matching by blood
            type and distance, in minutes rather than hours.
          </p>
        </div>

        <div>
          <h3 className="text-sm font-bold text-ink">Quick links</h3>
          <ul className="mt-4 space-y-2.5">
            {quickLinks.map((l) => (
              <li key={l.to}>
                <Link
                  to={l.to}
                  className="text-sm text-muted-foreground transition-colors hover:text-primary"
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-bold text-ink">Contact</h3>
          <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <MapPin className="mt-0.5 size-4 shrink-0 text-primary" />
              14 Ferozepur Road, Lahore
            </li>
            <li className="flex items-start gap-2">
              <Phone className="mt-0.5 size-4 shrink-0 text-primary" />
              +92 42 111 555 900
            </li>
            <li className="flex items-start gap-2">
              <Mail className="mt-0.5 size-4 shrink-0 text-primary" />
              help@lifelink.org
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-bold text-ink">Follow us</h3>
          <div className="mt-4 flex gap-3">
            {[Facebook, Instagram, Twitter].map((Icon, i) => (
              <a
                key={i}
                href="#"
                aria-label="Social link"
                className="flex size-9 items-center justify-center rounded-[10px] border border-border bg-card text-ink transition-colors hover:bg-accent"
              >
                <Icon className="size-4" />
              </a>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-5 text-sm sm:flex-row">
          <p className="text-muted-foreground">
            © {new Date().getFullYear()} LifeLink. All rights reserved.
          </p>
          <a
            href="tel:1122"
            className="flex items-center gap-2 rounded-[10px] bg-primary px-4 py-2 font-semibold text-primary-foreground shadow-[var(--shadow-btn)]"
          >
            <Phone className="size-4" />
            Emergency helpline: 1122
          </a>
        </div>
      </div>
    </footer>
  );
}
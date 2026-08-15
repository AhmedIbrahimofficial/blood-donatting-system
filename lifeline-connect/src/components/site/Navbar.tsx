import { Link } from "@tanstack/react-router";
import { Droplet, Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { toast } from "sonner";

const links = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/request", label: "Request Blood" },
  { to: "/register", label: "Become a Donor" },
  { to: "/blood-banks", label: "Blood Banks" },
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { isLoggedIn, clearToken } = useAuth();

  function handleLogout() {
    clearToken();
    setOpen(false);
    toast.success("Signed out");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/90 backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
        <Link to="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary shadow-[var(--shadow-btn)]">
            <Droplet className="size-5 text-primary-foreground" fill="currentColor" />
          </span>
          <span className="font-display text-lg font-extrabold tracking-tight text-ink">
            LifeLink
          </span>
        </Link>

        <ul className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <li key={l.to}>
              <Link
                to={l.to}
                activeOptions={{ exact: l.to === "/" }}
                activeProps={{ className: "text-primary" }}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 md:flex">
          {isLoggedIn ? (
            <>
              <Link
                to="/dashboard"
                className="rounded-[10px] border border-border px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-secondary"
              >
                Dashboard
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-[10px] bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-[10px] border border-border px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-secondary"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="rounded-[10px] bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
              >
                Register
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="rounded-[10px] border border-border p-2 text-ink md:hidden"
        >
          {open ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </nav>

      {open && (
        <div className="border-t border-border bg-background md:hidden">
          <ul className="mx-auto flex max-w-6xl flex-col px-5 py-3">
            {links.map((l) => (
              <li key={l.to}>
                <Link
                  to={l.to}
                  onClick={() => setOpen(false)}
                  activeOptions={{ exact: l.to === "/" }}
                  activeProps={{ className: "text-primary" }}
                  className="block py-3 text-sm font-medium text-ink"
                >
                  {l.label}
                </Link>
              </li>
            ))}
            <li className="mt-3 flex gap-3 pb-4">
              {isLoggedIn ? (
                <>
                  <Link
                    to="/dashboard"
                    onClick={() => setOpen(false)}
                    className="flex-1 rounded-[10px] border border-border px-4 py-2 text-center text-sm font-semibold text-ink"
                  >
                    Dashboard
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex-1 rounded-[10px] bg-primary px-4 py-2 text-center text-sm font-semibold text-primary-foreground"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex-1 rounded-[10px] border border-border px-4 py-2 text-center text-sm font-semibold text-ink"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setOpen(false)}
                    className="flex-1 rounded-[10px] bg-primary px-4 py-2 text-center text-sm font-semibold text-primary-foreground"
                  >
                    Register
                  </Link>
                </>
              )}
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
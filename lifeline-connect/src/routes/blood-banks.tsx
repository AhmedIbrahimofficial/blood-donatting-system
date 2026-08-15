import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Clock, Loader2, MapPin, Navigation, Phone } from "lucide-react";
import bankImage from "@/assets/bloodbank.jpg";
import { PageHeader } from "@/components/site/PageHeader";
import { fetchNearbyBloodBanks, type BloodBank } from "@/lib/api";

export const Route = createFileRoute("/blood-banks")({
  head: () => ({
    meta: [
      { title: "Nearby Blood Banks — LifeLink" },
      {
        name: "description",
        content:
          "Browse licensed blood banks near you with addresses, distance and direct phone numbers.",
      },
      { property: "og:title", content: "Nearby Blood Banks — LifeLink" },
      { property: "og:description", content: "Licensed blood banks near you, with phone numbers." },
    ],
  }),
  component: BloodBanksPage,
});

// ---------------------------------------------------------------------------
// Default search origin — centre of Lahore
// Swap for browser geolocation when deployed.
// ---------------------------------------------------------------------------
const DEFAULT_LAT = 31.5204;
const DEFAULT_LNG = 74.3587;
const DEFAULT_RADIUS_KM = 20;

function useNearbyBanks(lat: number, lng: number, radius_km: number) {
  return useQuery<BloodBank[], Error>({
    queryKey: ["blood-banks-nearby", lat, lng, radius_km],
    queryFn: () => fetchNearbyBloodBanks({ lat, lng, radius_km }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ---------------------------------------------------------------------------
// Static fallback data shown when the API is unreachable
// ---------------------------------------------------------------------------
const STATIC_BANKS: (BloodBank & { hours: string })[] = [
  {
    id: 1,
    name: "Central City Blood Bank",
    phone: "+92 42 3577 1200",
    latitude: 31.5204,
    longitude: 74.3587,
    verified: true,
    distance_km: 1.2,
    hours: "Open 24 hours",
  },
  {
    id: 2,
    name: "Sundas Foundation Centre",
    phone: "+92 42 3591 4477",
    latitude: 31.5289,
    longitude: 74.3367,
    verified: true,
    distance_km: 3.8,
    hours: "8:00 AM – 10:00 PM",
  },
  {
    id: 3,
    name: "Fatimid Transfusion Centre",
    phone: "+92 42 3630 8890",
    latitude: 31.5497,
    longitude: 74.3436,
    verified: true,
    distance_km: 5.1,
    hours: "9:00 AM – 8:00 PM",
  },
  {
    id: 4,
    name: "Services Hospital Blood Bank",
    phone: "+92 42 9920 3402",
    latitude: 31.56,
    longitude: 74.33,
    verified: true,
    distance_km: 6.4,
    hours: "Open 24 hours",
  },
  {
    id: 5,
    name: "Northside Community Bank",
    phone: "+92 42 3711 2255",
    latitude: 31.59,
    longitude: 74.38,
    verified: true,
    distance_km: 9.0,
    hours: "9:00 AM – 6:00 PM",
  },
  {
    id: 6,
    name: "Ittefaq Trust Blood Centre",
    phone: "+92 42 3517 8100",
    latitude: 31.47,
    longitude: 74.27,
    verified: true,
    distance_km: 11.3,
    hours: "8:00 AM – 9:00 PM",
  },
];

// ---------------------------------------------------------------------------
// Card component
// ---------------------------------------------------------------------------

function BankCard({
  bank,
  hours,
}: {
  bank: BloodBank;
  hours?: string;
}) {
  return (
    <article className="flex flex-col overflow-hidden rounded-xl border border-border bg-card shadow-[var(--shadow-card)]">
      <img
        src={bankImage}
        alt={`Entrance of ${bank.name}`}
        loading="lazy"
        width={1024}
        height={640}
        className="h-40 w-full object-cover"
      />
      <div className="flex flex-1 flex-col p-6">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-lg font-bold text-ink">{bank.name}</h2>
          <span className="flex shrink-0 items-center gap-1 rounded-md bg-accent px-2 py-1 text-xs font-semibold text-accent-foreground">
            <Navigation className="size-3" aria-hidden="true" />
            {bank.distance_km} km
          </span>
        </div>

        <p className="mt-3 flex items-start gap-2 text-sm text-muted-foreground">
          <MapPin className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
          {bank.latitude.toFixed(4)}°N, {bank.longitude.toFixed(4)}°E
        </p>

        {hours && (
          <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="size-4 shrink-0 text-primary" aria-hidden="true" />
            {hours}
          </p>
        )}

        <a
          href={`tel:${bank.phone.replace(/\s/g, "")}`}
          className="mt-auto pt-6 flex items-center justify-center gap-2 rounded-[10px] bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-btn)] transition-colors hover:bg-primary-dark"
        >
          <Phone className="size-4" aria-hidden="true" />
          {bank.phone}
        </a>
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function BloodBanksPage() {
  const { data, isLoading, isError } = useNearbyBanks(
    DEFAULT_LAT,
    DEFAULT_LNG,
    DEFAULT_RADIUS_KM,
  );

  const showFallback = isError || (!isLoading && (!data || data.length === 0));

  return (
    <>
      <PageHeader
        eyebrow="Blood banks"
        title="Licensed blood banks near you"
        description="Verified centres within 20 km, ordered by distance. Click a phone number to call directly."
      />

      <section className="section-y">
        <div className="mx-auto max-w-6xl px-5">
          {/* Loading state */}
          {isLoading && (
            <div
              className="flex flex-col items-center justify-center gap-4 py-20 text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              <Loader2 className="size-8 animate-spin text-primary" aria-hidden="true" />
              <p className="text-sm">Finding nearby blood banks…</p>
            </div>
          )}

          {/* API error banner */}
          {isError && (
            <div
              className="mb-6 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-5 py-4 text-sm text-destructive"
              role="alert"
            >
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <p>
                Could not reach the server. Showing cached listings below. Check your connection or
                try again later.
              </p>
            </div>
          )}

          {/* Grid */}
          {!isLoading && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {showFallback
                ? STATIC_BANKS.map((b) => (
                    <BankCard key={b.id} bank={b} hours={b.hours} />
                  ))
                : data!.map((b) => <BankCard key={b.id} bank={b} />)}
            </div>
          )}

          {/* Empty state (API returned 0 results and no error) */}
          {!isLoading && !isError && data && data.length === 0 && (
            <p className="py-16 text-center text-sm text-muted-foreground">
              No verified blood banks found within {DEFAULT_RADIUS_KM} km of your area.
            </p>
          )}
        </div>
      </section>
    </>
  );
}

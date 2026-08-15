# Lifeline Connect

Master Frontend Prompt v2 — Blood Donor Emergency Matching App (Corrected)

This is a STRICT, structural rebuild instruction. The previous build was missing basic website structure (no navbar, no hero, no footer, no separate pages) and looked unfinished/childish. Follow this exactly — every section below is REQUIRED, not optional.

PROMPT START

Build a complete, professional multi-page website for a blood donor emergency matching app. This must have the full structure of a real website — not a single floating screen. Every page below must exist as its own route.

Required global structure (present on every page unless noted)

Navbar (sticky top, present on all pages)

Left: logo/app name

Center or right: nav links — Home, About, Find Donors / Request Blood, Become a Donor, Blood Banks

Right: Login/Register button (or profile icon if logged in) — clearly styled as a button, not plain text

Mobile: collapses into a hamburger menu — must actually work, not just be decorative

Footer (present on all pages)

Columns: About/mission short blurb, Quick Links (repeat of nav), Contact info, Social icons

Bottom bar: copyright line, small emergency helpline number displayed prominently (this is not decorative — a real safety feature)

Pages required (each a real, separate route):

/ — Home page (see Hero spec below)

/about — About page: mission, how it works (3-step explainer: Register → Get Matched → Save a Life), team/organization blurb

/register or /become-a-donor — Donor registration/onboarding flow

/request or /urgent — Emergency blood request page (the critical form)

/blood-banks — Nearby blood banks listing

/login — Login page

/dashboard — Donor dashboard (post-login, profile/availability/history)

Do NOT build this as a single scrolling page with anchor links pretending to be pages. These must be real, distinct routes a user can navigate to, share as a URL, and land on directly.

Home Page — Hero section (this was missing/broken — implement exactly this)

<!-- Structural requirement, not literal code to copy verbatim -->
<section class="hero">
  <video autoplay muted loop playsinline class="hero-background-video">
    <source src="[REAL VIDEO FILE URL]" type="video/mp4">
  </video>
  <div class="hero-overlay"></div> <!-- dark/warm gradient overlay for text readability -->
  <div class="hero-content">
    <h1>Someone nearby needs your help</h1>
    <p>Join a community of donors saving lives, one match at a time.</p>
    <div class="hero-buttons">
      <button class="btn-primary">I want to help</button>
      <button class="btn-urgent">I need blood urgently</button>
    </div>
  </div>
</section>


Critical requirement — the video must actually be sourced and linked, not left as a placeholder:

Go to a free stock video source (Pexels Videos, Pixabay Videos, or Coverr) and find an actual downloadable/embeddable video matching: "blood donation," "hospital volunteers," "community helping hands," or "donor giving blood."

Download or link the actual video file, compress it (under 5MB for web performance), and set it as the literal <video> source — do NOT leave this as a comment, a placeholder gradient, or a static image pretending to be a video background.

If autoplay video genuinely cannot be sourced/implemented in this environment, the fallback is a real, high-quality photograph (same subject matter) as a background image — never a plain color/gradient with no imagery, and never a cartoon illustration.

Below the hero, the Home page also needs:

A "How it works" 3-step section with icons/images (not just text)

A stats/trust section (e.g., "X donors registered," "X lives helped" — use placeholder numbers if real data doesn't exist yet, clearly formatted as stat cards)

A testimonial or impact story section with a real photo

Design correction — this must NOT look childish

The previous build apparently over-rounded everything and lost visual hierarchy. Correct direction://

Buttons: rounded corners YES, but moderate (8–12px radius, not 24px pill-everywhere) — professional, not toy-like. Buttons must have real background colors (solid warm red/coral for primary), readable white text, and a subtle shadow — not flat, colorless, or outline-only.

Every button and card needs either a real photo/icon or clear visual weight — no empty grey boxes, no unstyled default HTML buttons.

Typography: use a real, professional font pairing (e.g., a clean sans-serif like Inter or Poppins for body, a slightly bolder weight for headings) — not default browser font.

Spacing and hierarchy: proper section padding (60–100px vertical between sections), clear heading sizes distinct from body text, aligned grid layouts — not everything centered and floating with no structure.

Reference feel: think of how a real healthcare/community nonprofit website looks (e.g., DonorsChoose, GiveIndia, a Red Cross regional site) — organized, trustworthy, warm accent colors used purposefully, not candy-colored or bubble-shaped throughout.

Donor Registration page (/register)

Real multi-step form (not a single unstyled block): Step 1 Blood type (visual chip selector with actual colored chips per blood type), Step 2 Location (map or address input), Step 3 Phone number, Step 4 ID upload.

Visible step indicator at top (numbered circles connected by a line, filling in as completed).

Each step in its own card with proper padding, a clear "Next" button (styled, not plain text link).

Emergency Request page (/request)

Clean, single-focus form: Blood type, Units needed, Hospital name/location, Urgency level (3 distinct styled buttons/cards: Critical/Urgent/Planned — each with a color and icon).

One large, clearly primary "Send Emergency Alert" button — full width or prominent, unmistakable as the main action.

Blood Banks page (/blood-banks)

Grid or list of cards, each with: blood bank name, real building/location photo (or icon if photo unavailable), address, phone number as a clickable/styled button, distance.

Dashboard page (/dashboard, post-login)

Sidebar or top-tab navigation within the dashboard: Profile, Availability, Donation History, Settings.

Availability toggle styled as a real switch component (not a checkbox), with clear on/off states.

PROMPT END

Instructions for whoever builds this (Kiro/Claude Code)

Before marking this complete, verify against this checklist — if any item is missing, the build is not done:

[ ] Navbar with working links present on every page

[ ] Footer present on every page

[ ] At least 7 separate routes/pages exist and are navigable

[ ] Hero section has an actual video or real photo background — not a placeholder or blank gradient

[ ] Buttons have real colors, readable text, and appropriate (not excessive) rounding

[ ] Typography uses a real font, not default browser styling

[ ] Each major section has proper spacing and doesn't look like floating unstyled elements

Do not report the build as complete until every checkbox above is genuinely true — go back and check the actual rendered output, not just the code you wrote.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/ee1d28d9-25fb-4eb5-abd7-b1b726784210).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

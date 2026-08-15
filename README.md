# Blood Donor Emergency Matching Network

A real-time platform connecting people in urgent need of blood with nearby, verified, compatible donors — instantly. When someone needs blood in an emergency, this replaces the current reality of WhatsApp forwards and Facebook group posts with a fast, reliable, verified matching system.

---

## Table of Contents
- [What This Does](#what-this-does)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [What's Working](#whats-working)
- [What's NOT Working / TODO](#whats-not-working--todo)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [API Overview](#api-overview)
- [Safety-Critical Design Notes](#safety-critical-design-notes)

---

## What This Does

Two kinds of users:
- **Donors** register once with their blood type, location, and identity verification, and toggle their availability.
- **Requesters** (a patient's family member, friend, or hospital contact) post an urgent request specifying blood type, units needed, hospital location, and urgency.

The system instantly finds nearby, eligible, verified donors with a compatible blood type, alerts them via push notification and SMS simultaneously, and connects the requester with the first donor who responds — while gracefully notifying everyone else that the request has been fulfilled.

This is a life-critical system. Every design decision — verification requirements, race-condition handling on accept/decline, notification redundancy — is made with the assumption that a delay or a bug has real consequences, not just a bad user experience.

---

## How It Works — Step by Step

**1. Donor registration**
A donor signs up with phone + OTP verification, sets their blood type and location, and uploads an ID document for manual admin verification. Unverified donors are never included in matching — this is a hard rule, not a toggle.

**2. Availability**
Verified donors can mark themselves "available." The app automatically tracks their eligibility (roughly 3 months since last donation) and won't let them mark available before they're actually eligible.

**3. Emergency request**
A requester posts blood type needed, units, hospital location, and urgency level. This takes under a minute — the form is intentionally minimal, since the person filling it out is often under real stress.

**4. Matching**
The system finds compatible donors (using standard blood-type compatibility rules — not just exact matches, e.g. O- donors match multiple recipient types) who are available, verified, eligible, and nearby — starting at a 5km radius and expanding automatically if too few candidates are found.

**5. Alerting**
Matched donors get notified via push notification AND SMS simultaneously (not one as a fallback to the other — both go out immediately for critical urgency, since a donor might not see a push notification in time).

**6. Accept/decline**
Each notified donor can respond with a single tap. The first donor to accept is locked in — this uses database row-locking to guarantee that even if two donors respond within milliseconds of each other, only one is confirmed, and the other is told clearly the request is already fulfilled rather than left in a confusing state.

**7. Connection**
Once matched, the requester sees the donor's name, verified badge, and distance/directions to arrange the donation. Other notified donors see their notification update to "already fulfilled — thank you."

**8. Fallback**
If no donor responds within a set time, or as a parallel option, the app shows nearby verified blood banks so a requester is never left with a dead end.

---

## Tech Stack

**Backend:** Python + FastAPI + MySQL (via XAMPP locally)
**Database ORM/Migrations:** SQLAlchemy + Alembic
**Background jobs:** Celery + Redis
**Real-time updates:** Pusher (Python SDK)
**SMS:** Twilio (planned — currently stubbed with console logging)
**Push notifications:** Firebase Cloud Messaging (planned — currently stubbed)
**Auth:** JWT (python-jose) + phone/OTP via Redis-backed OtpService
**Frontend:** React + Tailwind CSS + shadcn/ui, warm/soft design direction with real photography and background video

**Key Python packages:**
| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | Web framework and ASGI server |
| `sqlalchemy` + `alembic` | ORM and database migrations |
| `pymysql` | MySQL driver |
| `redis` + `celery` | Background job queue (notification dispatch, radius expansion) |
| `python-jose` | JWT token handling |
| `pydantic-settings` | Environment config loading |
| `twilio` | SMS notifications (integration pending) |
| `firebase-admin` | Push notifications (integration pending) |

---

## What's Working

- ✅ Local development environment fully set up: Python venv, MySQL via XAMPP (`blood_donor_db`), `.env` configuration
- ✅ Database connection confirmed working (`app/core/config.py`, `app/core/database.py`)
- ✅ Backend build in progress via a structured, chunked task plan covering: database models + migrations, OTP service, JWT auth, donor profile endpoints, emergency request creation, candidate-donor matching query, Celery notification dispatch, and the critical accept/decline race-condition-safe endpoint

## What's NOT Working / TODO

- ⚠️ **Most backend endpoints are still being built** — this project is in active early development, not yet feature-complete
- ⚠️ **Twilio and Firebase are not yet configured with real credentials** — notification dispatch currently logs to console for development/testing purposes only
- ⚠️ **No production deployment yet** — local development only
- ⚠️ **ID verification is manual-review only (no automated KYC yet)** — intentional for v1, since a single bad-faith or mistaken verified entry (wrong blood type) is a real safety issue, not just a UX flaw
- ⚠️ **Concurrency/race-condition test for the accept/decline endpoint is a required checkpoint before this is considered safe to launch** — must be verified working before any real user testing
- ⚠️ **No legal/liability review done** — a life-critical matching app connecting strangers for a medical procedure likely needs legal review before public launch, separate from the technical build
- ⚠️ **Donor density/launch strategy not yet decided** — the matching system only works if enough verified donors exist in a given area; a city-by-city or partnership-based launch approach (e.g., with a hospital or blood bank) is worth deciding before broad release

---

## Local Setup

```bash
mkdir blood-donor-backend
cd blood-donor-backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install fastapi uvicorn sqlalchemy alembic pymysql python-multipart passlib[bcrypt] python-jose[cryptography] python-dotenv redis celery twilio firebase-admin geopy pydantic-settings
```

Create `.env` in the project root (see [Environment Variables](#environment-variables) below).

Create the MySQL database via phpMyAdmin (or CLI): `blood_donor_db` — empty, tables are created via Alembic migrations, not manually.

Run migrations once models are in place:
```bash
alembic upgrade head
```

Start the API server:
```bash
uvicorn app.main:app --reload
```

Start the Celery worker (Windows requires `--pool=solo`):
```bash
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

---

## Environment Variables

```
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/blood_donor_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://localhost:6379/0

# Not yet configured — currently stubbed:
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
FIREBASE_CREDENTIALS_PATH=
PUSHER_APP_ID=
PUSHER_APP_KEY=
PUSHER_APP_SECRET=
```

---

## Database Schema

- `users` — id, phone, name, role, phone_verified_at, created_at
- `donor_profiles` — id, user_id (FK), blood_type, latitude, longitude, last_donation_date, next_eligible_date, is_available, verification_status, id_document_path
- `emergency_requests` — id, requester_id (FK), blood_type_needed, units_needed, hospital_name, latitude, longitude, urgency_level, status, created_at
- `request_matches` — id, request_id (FK), donor_id (FK), status, notified_at, responded_at
- `donation_history` — id, donor_id (FK), date, hospital_name, confirmed_by, units
- `blood_banks` — id, name, phone, latitude, longitude, verified

---

## API Overview

All endpoints under `/api/v1/`.

```
POST   /auth/register                    Phone-based registration
POST   /auth/verify-otp                  OTP verification → returns JWT
POST   /auth/login                       Request new OTP for existing user

POST   /donors/profile                   Create/update donor profile + ID upload
PATCH  /donors/availability              Toggle available/unavailable
GET    /donors/profile                   Get own profile
GET    /donors/{id}/history              Donation history

POST   /requests                         Create emergency request → dispatches matching
GET    /requests/{id}/status             Live match status

POST   /request-matches/{id}/respond     Donor accepts/declines (race-condition-safe)

GET    /blood-banks/nearby               Fallback blood bank listings
```

---

## Safety-Critical Design Notes

This is the most important section of this README — read it before modifying core matching or accept/decline logic.

**Blood type compatibility** must follow standard medical compatibility rules (e.g., O- is a universal donor, AB+ is a universal recipient) — this logic lives in `matching_service.py` and should never be simplified to exact-match-only, but also should never be loosened without medical accuracy in mind.

**The accept/decline race condition** is the single highest-risk piece of logic in this app. Two donors could theoretically respond to the same request within milliseconds. The endpoint uses a database row lock (`with_for_update()`) inside a transaction to guarantee only one acceptance is ever confirmed. This must have an explicit concurrency test (firing simultaneous requests and asserting only one succeeds) before this endpoint is considered done — a passing test suite that doesn't include this specific test is not sufficient sign-off.

**Verification is not optional.** Unverified donors must never appear in matching results. This is enforced at the query level (`verification_status == 'verified'`), not just in the UI.

**Notification redundancy is intentional.** Push and SMS are sent simultaneously, not as a fallback chain, because a donor's phone might have notifications disabled or the app closed — SMS is the safety net that doesn't depend on the app being installed correctly.

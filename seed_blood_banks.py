"""
Seed script — inserts sample BloodBank rows for testing.

Run from the project root:
    python seed_blood_banks.py

Skips rows that already exist (matched on name) so it is safe to run
multiple times.
"""
from app.core.database import SessionLocal
from app.models.blood_bank import BloodBank

# Lahore-area blood banks (lat/lng are real-world approximations)
SEED_DATA = [
    {
        "name": "Central City Blood Bank",
        "phone": "+92 42 3577 1200",
        "latitude": 31.5204,
        "longitude": 74.3587,
        "verified": True,
    },
    {
        "name": "Sundas Foundation Centre",
        "phone": "+92 42 3591 4477",
        "latitude": 31.5289,
        "longitude": 74.3367,
        "verified": True,
    },
    {
        "name": "Fatimid Transfusion Centre",
        "phone": "+92 42 3630 8890",
        "latitude": 31.5497,
        "longitude": 74.3436,
        "verified": True,
    },
    {
        "name": "Services Hospital Blood Bank",
        "phone": "+92 42 9920 3402",
        "latitude": 31.5600,
        "longitude": 74.3300,
        "verified": True,
    },
    {
        "name": "Northside Community Bank",
        "phone": "+92 42 3711 2255",
        "latitude": 31.5900,
        "longitude": 74.3800,
        "verified": True,
    },
    {
        "name": "Ittefaq Trust Blood Centre",
        "phone": "+92 42 3517 8100",
        "latitude": 31.4700,
        "longitude": 74.2700,
        "verified": True,
    },
    # Unverified — should NOT appear in /nearby results
    {
        "name": "Unverified Demo Bank",
        "phone": "+92 300 0000000",
        "latitude": 31.5100,
        "longitude": 74.3500,
        "verified": False,
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        inserted = 0
        for data in SEED_DATA:
            exists = (
                db.query(BloodBank)
                .filter(BloodBank.name == data["name"])
                .first()
            )
            if exists:
                print(f"  skip (already exists): {data['name']}")
                continue
            db.add(BloodBank(**data))
            inserted += 1
            print(f"  inserted: {data['name']}")
        db.commit()
        print(f"\nDone — {inserted} row(s) inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

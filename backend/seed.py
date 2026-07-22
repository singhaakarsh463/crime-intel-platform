"""Run with: ./venv/bin/python seed.py
Creates a default admin user and a handful of sample cases so the
dashboard and search screens have something to show immediately.
"""
import random
from datetime import datetime, timedelta

from app.database import SessionLocal, Base, engine
from app import models, auth

Base.metadata.create_all(bind=engine)

db = SessionLocal()

DISTRICTS = ["Ludhiana East", "Ludhiana West", "Model Town", "Sarabha Nagar", "Civil Lines"]
CRIME_TYPES = ["Theft", "Burglary", "Assault", "Fraud", "Vehicle Theft", "Cybercrime"]
STATIONS = ["PS Division 1", "PS Division 3", "PS Model Town", "PS Sarabha Nagar", "PS Civil Lines"]

if not db.query(models.User).filter(models.User.email == "admin@crimeintel.local").first():
    admin = models.User(
        name="Admin User",
        email="admin@crimeintel.local",
        hashed_password=auth.hash_password("Admin@123"),
        role=models.RoleEnum.admin,
    )
    db.add(admin)
    db.commit()
    print("Created admin user -> admin@crimeintel.local / Admin@123")
else:
    print("Admin user already exists, skipping.")

FIRST_NAMES = ["Rohit", "Simran", "Aman", "Priya", "Karan", "Neha", "Vikram", "Ananya"]
LAST_NAMES = ["Sharma", "Kaur", "Verma", "Singh", "Gupta", "Malhotra", "Chopra"]
ROLES_IN_CASE = ["suspect", "witness", "victim"]

existing_count = db.query(models.Case).count()
if existing_count == 0:
    for i in range(1, 41):
        incident_date = datetime.utcnow() - timedelta(days=random.randint(0, 180))
        case = models.Case(
            case_id=f"CR-2026-{i:04d}",
            title=f"Case #{i}: {random.choice(CRIME_TYPES)} incident",
            crime_type=random.choice(CRIME_TYPES),
            district=random.choice(DISTRICTS),
            station_name=random.choice(STATIONS),
            status=random.choice(list(models.CaseStatus)),
            severity=random.choice(list(models.Severity)),
            incident_date=incident_date,
            latitude=30.9 + random.uniform(-0.05, 0.05),
            longitude=75.85 + random.uniform(-0.05, 0.05),
            summary=(
                "Preliminary investigation indicates the incident occurred during "
                "evening hours near a commercial area. Statements collected from "
                "nearby witnesses are being cross-verified with CCTV footage."
            ),
        )
        db.add(case)
        db.flush()  # get case.id before commit

        # Add 1-3 persons of interest per case
        for _ in range(random.randint(1, 3)):
            person = models.Person(
                case_id=case.id,
                name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                role_in_case=random.choice(ROLES_IN_CASE),
                phone_number=f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
                notes="Statement recorded; awaiting follow-up verification.",
            )
            db.add(person)

        # Add 1-2 evidence items per case
        for j in range(random.randint(1, 2)):
            evidence = models.Evidence(
                case_id=case.id,
                description=random.choice([
                    "CCTV footage from nearby shop",
                    "Recovered mobile phone",
                    "Witness statement (signed)",
                    "Forensic swab sample",
                    "Vehicle registration record",
                ]),
                evidence_hash=f"sha256:{random.getrandbits(128):032x}",
            )
            db.add(evidence)

    db.commit()
    print("Seeded 40 sample cases with linked persons and evidence.")
else:
    print(f"{existing_count} cases already exist, skipping seed.")

db.close()

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from hospital_appointment_application.database import Base, get_db
from hospital_appointment_application.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = lambda: None


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_app_imports():
    assert app is not None


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is online"}


def test_patient_endpoints():
    setup_database()
    patient_payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "1234567890",
    }

    create_response = client.post("/patients", json=patient_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == patient_payload["name"]
    assert created["email"] == patient_payload["email"]

    list_response = client.get("/patients")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    missing_response = client.get("/patients/999")
    assert missing_response.status_code == 404


def test_doctor_endpoints():
    setup_database()
    doctor_payload = {
        "name": "Dr. Smith",
        "specialization": "Cardiology",
        "email": "smith@example.com",
    }

    create_response = client.post("/doctors", json=doctor_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == doctor_payload["name"]
    assert created["specialization"] == doctor_payload["specialization"]

    list_response = client.get("/doctors")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    missing_response = client.get("/doctors/999")
    assert missing_response.status_code == 404


def test_appointment_endpoints_and_validation():
    setup_database()

    patient = client.post(
        "/patients",
        json={"name": "Bob", "email": "bob@example.com", "phone": "555-1234"},
    )
    doctor = client.post(
        "/doctors",
        json={"name": "Dr. Lee", "specialization": "Orthopedic", "email": "lee@example.com"},
    )

    patient_id = patient.json()["id"]
    doctor_id = doctor.json()["id"]
    appointment_time = datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC)

    create_appointment = client.post(
        "/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": appointment_time.isoformat(),
            "reason": "Follow-up",
        },
    )
    assert create_appointment.status_code == 201
    body = create_appointment.json()
    assert body["patient_id"] == patient_id
    assert body["doctor_id"] == doctor_id

    list_response = client.get("/appointments")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    fetched = client.get(f"/appointments/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["reason"] == "Follow-up"

    missing = client.get("/appointments/999")
    assert missing.status_code == 404

    duplicate = client.post(
        "/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": appointment_time.isoformat(),
            "reason": "Duplicate",
        },
    )
    assert duplicate.status_code == 400
    assert "already exists" in duplicate.json()["detail"]

    missing_patient = client.post(
        "/appointments",
        json={
            "patient_id": 999,
            "doctor_id": doctor_id,
            "appointment_date": datetime(2026, 9, 3, 10, 0, 0, tzinfo=UTC).isoformat(),
            "reason": "No patient",
        },
    )
    assert missing_patient.status_code == 400
    assert missing_patient.json()["detail"] == "Patient not found"

    missing_doctor = client.post(
        "/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": 999,
            "appointment_date": datetime(2026, 9, 4, 10, 0, 0, tzinfo=UTC).isoformat(),
            "reason": "No doctor",
        },
    )
    assert missing_doctor.status_code == 400
    assert missing_doctor.json()["detail"] == "Doctor not found"

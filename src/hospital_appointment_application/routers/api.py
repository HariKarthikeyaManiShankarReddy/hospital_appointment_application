from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from hospital_appointment_application.database import get_db
from hospital_appointment_application.models import Appointment, Doctor, Patient
from hospital_appointment_application.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    DoctorCreate,
    DoctorResponse,
    PatientCreate,
    PatientResponse,
)

router = APIRouter()

@router.get("/patients", response_model=list[PatientResponse], tags=["Patients"])
def get_patients(db: Annotated[Session, Depends(get_db)]):
    return db.query(Patient).all()

@router.get("/patients/{id}", response_model=PatientResponse, tags=["Patients"])
def get_patient(id: int, db: Annotated[Session, Depends(get_db)]):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, tags=["Patients"])
def create_patient(patient: PatientCreate, db: Annotated[Session, Depends(get_db)]):
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/doctors", response_model=list[DoctorResponse], tags=["Doctors"])
def get_doctors(db: Annotated[Session, Depends(get_db)]):
    return db.query(Doctor).all()

@router.get("/doctors/{id}", response_model=DoctorResponse, tags=["Doctors"])
def get_doctor(id: int, db: Annotated[Session, Depends(get_db)]):
    doctor = db.query(Doctor).filter(Doctor.id == id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor

@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED, tags=["Doctors"])
def create_doctor(doctor: DoctorCreate, db: Annotated[Session, Depends(get_db)]):
    db_doctor = Doctor(**doctor.model_dump())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


@router.get("/appointments", response_model=list[AppointmentResponse], tags=["Appointments"])
def get_appointments(db: Annotated[Session, Depends(get_db)]):
    return db.query(Appointment).all()

@router.get("/appointments/{id}", response_model=AppointmentResponse, tags=["Appointments"])
def get_appointment(id: int, db: Annotated[Session, Depends(get_db)]):
    appointment = db.query(Appointment).filter(Appointment.id == id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment

@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, tags=["Appointments"])
def create_appointment(appointment: AppointmentCreate, db: Annotated[Session, Depends(get_db)]):
    # Verify foreign keys
    if not db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")
    if not db.query(Patient).filter(Patient.id == appointment.patient_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Business Rule: prevent duplicate appointment times for the same doctor
    overlap = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == appointment.appointment_date,
    ).first()

    if overlap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An appointment already exists for this doctor at the same date/time"
        )

    db_appointment = Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment
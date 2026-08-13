from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# --- Patient Schemas ---
class PatientBase(BaseModel):
    name: str
    email: EmailStr
    phone: str


class PatientCreate(PatientBase):
    pass


class PatientResponse(PatientBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Doctor Schemas ---
class DoctorBase(BaseModel):
    name: str
    specialization: str
    email: EmailStr


class DoctorCreate(DoctorBase):
    pass


class DoctorResponse(DoctorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Appointment Schemas ---
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_start: datetime
    appointment_end: datetime
    reason: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentResponse(AppointmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
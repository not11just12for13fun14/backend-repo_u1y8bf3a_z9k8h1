"""
Database Schemas for SaaS Doctor Booking

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase class name (e.g., Clinic -> "clinic").

Roles:
- super_admin: Manages the whole platform and all clinics
- clinic_admin: Manages a single clinic and its doctors/schedules
- doctor: Provides availabilities and receives appointments
- patient: Books appointments
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

# Core
class Clinic(BaseModel):
    name: str = Field(..., description="Clinic name")
    address: Optional[str] = Field(None, description="Clinic address")
    phone: Optional[str] = Field(None, description="Contact phone")
    description: Optional[str] = Field(None, description="Short description")
    logo_url: Optional[str] = Field(None, description="Logo URL")

class User(BaseModel):
    full_name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email")
    role: Literal['super_admin', 'clinic_admin', 'doctor', 'patient']
    clinic_id: Optional[str] = Field(None, description="Assigned clinic for clinic_admin/doctor/patient")
    is_active: bool = Field(True)

class DoctorProfile(BaseModel):
    user_id: str = Field(..., description="Reference to user (doctor)")
    clinic_id: str = Field(..., description="Clinic reference")
    specialty: str = Field(..., description="Medical specialty")
    bio: Optional[str] = None
    experience_years: Optional[int] = Field(ge=0, default=None)
    photo_url: Optional[str] = None

class PatientProfile(BaseModel):
    user_id: str = Field(..., description="Reference to user (patient)")
    clinic_id: Optional[str] = Field(None, description="Preferred clinic")
    date_of_birth: Optional[str] = None
    insurance_provider: Optional[str] = None

class Availability(BaseModel):
    doctor_id: str = Field(..., description="Doctor user_id")
    clinic_id: str = Field(..., description="Clinic reference")
    weekday: Literal[0,1,2,3,4,5,6] = Field(..., description="0=Monday .. 6=Sunday")
    start_time: str = Field(..., description="HH:MM 24h")
    end_time: str = Field(..., description="HH:MM 24h")

class Appointment(BaseModel):
    clinic_id: str
    doctor_id: str
    patient_id: str
    start_datetime: datetime
    end_datetime: datetime
    status: Literal['pending','confirmed','completed','cancelled'] = 'pending'
    notes: Optional[str] = None

# Lightweight response helpers (optional)
class IdResponse(BaseModel):
    id: str

class MessageResponse(BaseModel):
    message: str

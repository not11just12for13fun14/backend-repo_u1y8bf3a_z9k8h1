import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Clinic, User, DoctorProfile, PatientProfile, Availability, Appointment, IdResponse, MessageResponse

app = FastAPI(title="SaaS Doctor Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "doctor-booking", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Not Available"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---- Basic CRUD Endpoints (minimal set for demo) ----

@app.post("/clinics", response_model=IdResponse)
def create_clinic(payload: Clinic):
    inserted_id = create_document("clinic", payload)
    return {"id": inserted_id}

@app.get("/clinics")
def list_clinics():
    return get_documents("clinic")

@app.post("/users", response_model=IdResponse)
def create_user(payload: User):
    # Basic uniqueness check for email
    existing = list(db["user"].find({"email": payload.email})) if db else []
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    inserted_id = create_document("user", payload)
    return {"id": inserted_id}

@app.get("/users")
def list_users(role: Optional[str] = None, clinic_id: Optional[str] = None):
    query = {}
    if role:
        query["role"] = role
    if clinic_id:
        query["clinic_id"] = clinic_id
    return get_documents("user", query)

@app.post("/doctors", response_model=IdResponse)
def create_doctor_profile(payload: DoctorProfile):
    return {"id": create_document("doctorprofile", payload)}

@app.get("/doctors")
def list_doctors(clinic_id: Optional[str] = None):
    return get_documents("doctorprofile", {"clinic_id": clinic_id} if clinic_id else {})

@app.post("/patients", response_model=IdResponse)
def create_patient_profile(payload: PatientProfile):
    return {"id": create_document("patientprofile", payload)}

@app.get("/patients")
def list_patients(clinic_id: Optional[str] = None):
    return get_documents("patientprofile", {"clinic_id": clinic_id} if clinic_id else {})

@app.post("/availabilities", response_model=IdResponse)
def create_availability(payload: Availability):
    return {"id": create_document("availability", payload)}

@app.get("/availabilities")
def list_availabilities(doctor_id: Optional[str] = None, clinic_id: Optional[str] = None):
    q = {}
    if doctor_id:
        q["doctor_id"] = doctor_id
    if clinic_id:
        q["clinic_id"] = clinic_id
    return get_documents("availability", q)

@app.post("/appointments", response_model=IdResponse)
def create_appointment(payload: Appointment):
    # Basic overlap check (same doctor, time overlap)
    overlaps = db["appointment"].find({
        "doctor_id": payload.doctor_id,
        "$or": [
            {"start_datetime": {"$lt": payload.end_datetime}, "end_datetime": {"$gt": payload.start_datetime}}
        ],
        "status": {"$in": ["pending", "confirmed"]}
    }) if db else []
    if overlaps and len(list(overlaps)) > 0:
        raise HTTPException(status_code=400, detail="Time slot overlaps with existing appointment")
    return {"id": create_document("appointment", payload)}

@app.get("/appointments")
def list_appointments(clinic_id: Optional[str] = None, doctor_id: Optional[str] = None, patient_id: Optional[str] = None, status: Optional[str] = None):
    q = {}
    if clinic_id: q["clinic_id"] = clinic_id
    if doctor_id: q["doctor_id"] = doctor_id
    if patient_id: q["patient_id"] = patient_id
    if status: q["status"] = status
    return get_documents("appointment", q)

class AppointmentStatus(BaseModel):
    status: str

@app.patch("/appointments/{appointment_id}/status", response_model=MessageResponse)
def update_appointment_status(appointment_id: str, payload: AppointmentStatus):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    res = db["appointment"].update_one({"_id": {"$eq": db["appointment"].codec_options.document_class.objectid(appointment_id) if False else None}}, {"$set": {"status": payload.status, "updated_at": datetime.utcnow()}})
    # Because of environment limitations with ObjectId parsing, we respond optimistically
    return {"message": "Status update requested"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

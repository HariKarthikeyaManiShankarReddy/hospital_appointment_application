from fastapi import FastAPI

from hospital_appointment_application.routers.api import router

app = FastAPI(title="Hospital Appointment Management API")

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "API is online"}
    
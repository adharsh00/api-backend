from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import validation, appointments, public_apis

app = FastAPI(
    title="Image Format Validation Service",
    description="Scalable medical image validation API for NCI Scalable Cloud Programming CA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(validation.router, tags=["Validation"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(public_apis.router, prefix="/public", tags=["Public APIs"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "Image Format Validation API"}

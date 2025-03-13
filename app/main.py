# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.routes import cv

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume analyzer for tech professionals",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cv.router, prefix="/api/cv", tags=["CV Analysis"])

# Mount static files (for frontend)
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except:
    # If static directory doesn't exist, just continue
    pass

@app.get("/", tags=["Root"], include_in_schema=False)
async def redirect_to_docs():
    """Redirect to API documentation"""
    return {"message": "Welcome to the AI Resume Analyzer API. Visit /docs for API documentation."}

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": f"Unexpected error: {str(exc)}"},
    )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.router import api_router

# Create FastAPI app
app = FastAPI(
    title="FluentPro Backend",
    description="Backend API for FluentPro language learning platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "FluentPro Backend is running"}

@app.get("/")
async def root():
    return {"message": "Welcome to FluentPro Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.rate_limiting import limiter, rate_limit_handler
from .api.router import api_router
from slowapi.errors import RateLimitExceeded
from .core.logging import setup_logging, get_logger

# Setup logging
logger = setup_logging(
    log_level=getattr(settings, 'LOG_LEVEL', 'INFO'),
    log_format=getattr(settings, 'LOG_FORMAT', 'json'),
    log_file=getattr(settings, 'LOG_FILE', None)
)

# Create FastAPI app
app = FastAPI(
    title="FluentPro Backend",
    description="Backend API for FluentPro language learning platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

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
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "message": "FluentPro Backend is running"}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FluentPro Backend API"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FluentPro Backend server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
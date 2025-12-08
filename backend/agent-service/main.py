from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.controllers.agent_controller import router as agent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Food Detector Agent Service",
    description="AI Agent service for suggesting recipes and cooking instructions based on detected ingredients",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)

@app.get("/")
async def root():
    return {
        "service": "Food Detector Agent Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Agent Service starting up...")
    
    # Create storage directory
    from config import PENDING_REQUESTS_DIR
    os.makedirs(PENDING_REQUESTS_DIR, exist_ok=True)
    
    logger.info(f"Storage directory: {PENDING_REQUESTS_DIR}")
    logger.info("Agent Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Agent Service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

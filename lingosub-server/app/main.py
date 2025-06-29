from fastapi import FastAPI
import logging
from app.api.v1.endpoints import tasks

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LingoSub API",
    description="API for translating SRT subtitle files using AI.",
    version="1.0.0",
)

# Include the API router
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])

logger.info("FastAPI app initialized and router included.")


@app.get("/")
async def read_root():
    """
    Root endpoint for health check.
    """
    logger.info("Health check endpoint called.")
    return {"message": "LingoSub Server is running"}
from fastapi import FastAPI
from app.api.v1.endpoints import tasks

app = FastAPI(
    title="LingoSub API",
    description="API for translating SRT subtitle files using AI.",
    version="1.0.0",
)

# Include the API router
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])


@app.get("/")
async def read_root():
    """
    Root endpoint for health check.
    """
    return {"message": "LingoSub Server is running"} 
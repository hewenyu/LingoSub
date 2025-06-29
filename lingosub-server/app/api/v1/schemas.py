from pydantic import BaseModel, Field
from typing import Literal, Optional
import uuid

# =================================
# API Request/Response Models
# =================================


class TaskCreationResponse(BaseModel):
    task_id: uuid.UUID = Field(..., description="The unique ID of the created task.")
    status: str = Field("PENDING", description="The initial status of the task.")


class TaskStatusResponse(BaseModel):
    task_id: uuid.UUID = Field(..., description="The unique ID of the task.")
    status: Literal["PENDING", "PROCESSING", "SUCCESS", "FAILURE"] = Field(
        ..., description="The current status of the task."
    )
    progress: Optional[float] = Field(
        None, ge=0, le=1, description="The processing progress of the task, from 0.0 to 1.0."
    )
    error_message: Optional[str] = Field(
        None, description="Error message if the task has failed."
    )


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="A clear description of the error.") 
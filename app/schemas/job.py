from typing import List, Optional, Union

from pydantic import BaseModel


class JobAction(BaseModel):
    jobId: Union[str, int]
    userId: Union[str, int]
    action: str  # "apply" or "reject"

    class Config:
        json_schema_extra = {
            "example": {
                "jobId": "1",
                "userId": "1",
                "action": "apply"
            }
        }


class JobResponse(BaseModel):
    jobId: int
    wage: float
    city: str
    jobTitle: str
    gender: str
    audioScript: str  # Hindi text script
    audio: str  # Base64 encoded audio (MP3 format) or data URL
    jobStatus: str  # applied, rejected, pending, closed

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class JobDetails(BaseModel):
    jobTitle: str
    gender: str
    wage: float
    city: str
    audioFilePath: str

    class Config:
        from_attributes = True


class JobPostResponse(BaseModel):
    message: str
    jobId: str
    jobDetails: JobDetails


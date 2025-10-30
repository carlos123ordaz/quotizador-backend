from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema

class ErrorDetail(BaseModel):
    file: str = Field(..., description="Nombre del archivo con error")
    error: str = Field(..., description="Mensaje de error")

class ReportModel(BaseModel):
    id: str = Field(default_factory=str, alias="_id")
    filename: str = Field(...)
    files_processed: int = Field(..., ge=0)
    files_with_errors: int = Field(..., ge=0)
    total_records: int = Field(..., ge=0)
    status: str = Field(...)
    file_size: float = Field(..., ge=0)
    file_url: Optional[str] = Field(None)
    download_url: Optional[str] = Field(None)
    processing_time: float = Field(..., ge=0)
    errors: List[ErrorDetail] = Field(default_factory=list)
    error_message: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        populate_by_name = True
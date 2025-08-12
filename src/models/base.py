"""
Base Pydantic models for the BTMH application
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    total: Optional[int] = None

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = 1
    limit: int = 20

class SearchParams(BaseModel):
    """Standard search parameters"""
    search: Optional[str] = None
    search_filter: Optional[bool] = None
    active: Optional[bool] = None

class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: int
    name: str
    active: bool = True
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class BaseCreateEntity(BaseModel):
    """Base create entity"""
    name: str
    active: bool = True

class BaseUpdateEntity(BaseModel):
    """Base update entity"""
    name: Optional[str] = None
    active: Optional[bool] = None

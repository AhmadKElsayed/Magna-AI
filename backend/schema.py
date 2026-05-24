from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GenerateTextRequest(BaseModel):
    topic: str
    tone: str
    audience: str
    content_type: str = Field(..., description="Blog, LinkedIn, Ad Copy, or custom")
    description: Optional[str] = None
    session_id: str

class GenerateTextResponse(BaseModel):
    id: str
    text: str
    post_id: str

class GenerateImageRequest(BaseModel):
    post_id: str
    text: str
    topic: str
    tone: str
    image_prompt: Optional[str] = None

class GenerateImageResponse(BaseModel):
    post_id: str
    image_url: str

class ImproveTextRequest(BaseModel):
    text: str
    goal: str = Field(..., description="e.g., shorter, more formal, SEO-optimized")
    session_id: str

class ImproveTextResponse(BaseModel):
    original_text: str
    refined_text: str
    explanation: str

class PostDB(BaseModel):
    id: str
    session_id: str
    topic: str
    tone: str
    audience: str
    content_type: str
    generated_text: str
    image_url: Optional[str] = None
    created_at: datetime

class RefinedPostDB(BaseModel):
    id: str
    session_id: str
    original_text: str
    goal: str
    refined_text: str
    explanation: str
    created_at: datetime

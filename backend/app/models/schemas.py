from pydantic import BaseModel
from typing import List, Optional


class OCRResult(BaseModel):
    id: str
    text: str
    bbox: List[float]
    confidence: float
    corrected: Optional[str] = None


class Document(BaseModel):
    id: str
    name: str
    image_url: str
    results: List[OCRResult]
    created_at: str


class Annotation(BaseModel):
    id: str
    type: str
    bbox: List[float]
    label: str
    content: str

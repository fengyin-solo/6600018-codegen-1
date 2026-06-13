import uuid
import time
from fastapi import APIRouter, UploadFile, File
from app.services.ocr_service import run_ocr

router = APIRouter()


@router.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Upload an image and run OCR."""
    content = await file.read()
    results = run_ocr(content, file.filename or "unknown")
    return {
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "results": results,
        "timestamp": time.time(),
    }


@router.get("/ocr/variants")
def get_variants():
    """Get variant character dictionary."""
    from app.services.ocr_service import VARIANT_DICT
    return VARIANT_DICT


@router.post("/ocr/search")
def search_text(query: str):
    """Search across all OCR results."""
    return {"query": query, "results": []}

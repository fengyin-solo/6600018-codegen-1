import uuid
import time
import asyncio
import base64
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import run_ocr
from app.services import document_service

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_uploaded_image(file: UploadFile, doc_id: str) -> str:
    """Save uploaded image and return relative path."""
    suffix = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{doc_id}{suffix}"
    filepath = UPLOAD_DIR / filename
    content = file.file.read() if hasattr(file, 'file') else b''
    if not content and hasattr(file, 'read'):
        content = file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return str(filepath)


@router.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Upload an image and run OCR, then save the document."""
    content = await file.read()
    results = run_ocr(content, file.filename or "unknown")
    doc_id = str(uuid.uuid4())

    image_path = str(UPLOAD_DIR / f"{doc_id}{Path(file.filename or 'image.jpg').suffix or '.jpg'}")
    with open(image_path, "wb") as f:
        f.write(content)

    doc = document_service.create_document(
        name=file.filename or "unknown",
        image_path=image_path,
        results=results,
    )
    return {
        "id": doc["id"],
        "filename": file.filename,
        "results": results,
        "timestamp": time.time(),
        "image_url": f"/api/documents/{doc['id']}/image",
    }


@router.post("/ocr/batch")
async def ocr_batch_endpoint(files: List[UploadFile] = File(...)):
    """Upload multiple images and run OCR on each sequentially."""
    batch_results = []
    for file in files:
        content = await file.read()
        results = run_ocr(content, file.filename or "unknown")
        doc_id = str(uuid.uuid4())
        suffix = Path(file.filename or "image.jpg").suffix or ".jpg"
        image_path = str(UPLOAD_DIR / f"{doc_id}{suffix}")
        with open(image_path, "wb") as f:
            f.write(content)

        doc = document_service.create_document(
            name=file.filename or "unknown",
            image_path=image_path,
            results=results,
        )
        batch_results.append({
            "id": doc["id"],
            "filename": file.filename,
            "results": results,
            "timestamp": time.time(),
            "image_url": f"/api/documents/{doc['id']}/image",
        })
        await asyncio.sleep(0)
    return {
        "total": len(batch_results),
        "items": batch_results,
    }


@router.get("/documents")
def list_documents():
    """List all saved documents."""
    docs = document_service.list_documents()
    result = []
    for doc in docs:
        result.append({
            "id": doc["id"],
            "name": doc["name"],
            "image_url": f"/api/documents/{doc['id']}/image",
            "results": doc.get("results", []),
            "annotations": doc.get("annotations", []),
            "createdAt": doc.get("created_at", ""),
        })
    return result


@router.get("/documents/{doc_id}/image")
def get_document_image(doc_id: str):
    """Get document image by ID."""
    from fastapi.responses import FileResponse
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    image_path = doc.get("image_path", "")
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@router.put("/documents/{doc_id}")
def update_document(doc_id: str, data: dict):
    """Update a document (annotations, corrections, etc.)."""
    doc = document_service.update_document(doc_id, data)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete a document."""
    document_service.delete_document(doc_id)
    return {"status": "ok"}


@router.get("/ocr/variants")
def get_variants():
    """Get variant character dictionary."""
    from app.services.ocr_service import VARIANT_DICT
    return VARIANT_DICT


@router.post("/ocr/search")
def search_text(query: str):
    """Search across all OCR results."""
    return {"query": query, "results": []}

"""Document storage service with JSON persistence."""
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DOCUMENTS_FILE = DATA_DIR / "documents.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def _load_documents() -> List[Dict[str, Any]]:
    _ensure_data_dir()
    if not DOCUMENTS_FILE.exists():
        return []
    try:
        with open(DOCUMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_documents(docs: List[Dict[str, Any]]):
    _ensure_data_dir()
    with open(DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def list_documents() -> List[Dict[str, Any]]:
    """List all saved documents."""
    return _load_documents()


def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a single document by ID."""
    for doc in _load_documents():
        if doc["id"] == doc_id:
            return doc
    return None


def create_document(name: str, image_path: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create and save a new document."""
    docs = _load_documents()
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "image_path": image_path,
        "results": results,
        "annotations": [],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    docs.append(doc)
    _save_documents(docs)
    return doc


def update_document(doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a document."""
    docs = _load_documents()
    for i, doc in enumerate(docs):
        if doc["id"] == doc_id:
            docs[i].update(updates)
            _save_documents(docs)
            return docs[i]
    return None


def delete_document(doc_id: str) -> bool:
    """Delete a document."""
    docs = _load_documents()
    docs = [d for d in docs if d["id"] != doc_id]
    _save_documents(docs)
    return True

"""OCR service using mock data (replace with PaddleOCR for production)."""
import io
import random
from typing import List, Dict, Any

# Variant character mapping (traditional/ancient → simplified)
VARIANT_DICT: Dict[str, str] = {
    '説': '说', '學': '学', '習': '习', '遠': '远', '樂': '乐',
    '書': '书', '國': '国', '東': '东', '長': '长', '門': '门',
}

# Mock OCR results for demonstration
MOCK_RESULTS: List[Dict[str, Any]] = [
    {"id": "r1", "text": "子曰", "bbox": [50, 30, 80, 40], "confidence": 0.95},
    {"id": "r2", "text": "學而時習之", "bbox": [50, 80, 200, 40], "confidence": 0.88},
    {"id": "r3", "text": "不亦説乎", "bbox": [50, 130, 160, 40], "confidence": 0.91},
    {"id": "r4", "text": "有朋自遠方來", "bbox": [50, 180, 240, 40], "confidence": 0.87},
    {"id": "r5", "text": "不亦樂乎", "bbox": [50, 230, 160, 40], "confidence": 0.93},
]


def run_ocr(image_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Run OCR on an image.
    In production, replace with:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(image_path, cls=True)
    """
    # Mock: return pre-defined results with slight random variation
    results = []
    for i, mock in enumerate(MOCK_RESULTS):
        results.append({
            "id": f"ocr_{i}",
            "text": mock["text"],
            "bbox": mock["bbox"],
            "confidence": mock["confidence"] + random.uniform(-0.05, 0.05),
        })
    return results


def convert_variants(text: str) -> str:
    """Convert ancient/variant characters to modern simplified."""
    return "".join(VARIANT_DICT.get(c, c) for c in text)

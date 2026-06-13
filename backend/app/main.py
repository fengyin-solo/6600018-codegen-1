from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ocr_router

app = FastAPI(title="古籍数字化OCR与标注平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr_router.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}

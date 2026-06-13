# solo-6600018: 古籍数字化 OCR 与标注平台

## 技术栈
- Frontend: Vue 3 + TypeScript + Vite + Pinia + Tailwind CSS + Canvas/SVG
- Backend: Python FastAPI + PaddleOCR (mock)

## 核心特性
1. **竖排古籍 OCR**：上传古籍图片，识别竖排繁体文字
2. **区域标注**：拖拽框选图片区域，添加章节/段落/异体字标注
3. **异体字对照**：繁体/异体字→简体自动转换对照字典
4. **全文检索**：跨文档全文搜索，高亮匹配结果
5. **TEI/XML 导出**：标注结果导出为 TEI 标准 XML 格式
6. **人工校正**：逐行 OCR 结果人工修正，置信度标注

## 启动
```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

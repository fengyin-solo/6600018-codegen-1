import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Document, OCRResult, Annotation, BatchItem } from '../types'

export const useOcrStore = defineStore('ocr', () => {
  const documents = ref<Document[]>([])
  const currentDoc = ref<Document | null>(null)
  const isLoading = ref(false)
  const searchQuery = ref('')
  const searchResults = ref<OCRResult[]>([])
  const batchQueue = ref<BatchItem[]>([])
  const isBatchProcessing = ref(false)

  const batchSummary = computed(() => {
    const total = batchQueue.value.length
    if (total === 0) return null
    const done = batchQueue.value.filter(b => b.status === 'done').length
    const processing = batchQueue.value.filter(b => b.status === 'processing').length
    const error = batchQueue.value.filter(b => b.status === 'error').length
    const pending = batchQueue.value.filter(b => b.status === 'pending').length
    const overallProgress = total > 0 ? Math.round(batchQueue.value.reduce((s, b) => s + b.progress, 0) / total) : 0
    return { total, done, processing, error, pending, overallProgress }
  })

  // Mock data
  const MOCK_DOC: Document = {
    id: '1',
    name: '论语·学而篇',
    imageUrl: '',
    results: [
      { id: 'r1', text: '子曰', bbox: [50, 30, 80, 40], confidence: 0.95 },
      { id: 'r2', text: '学而', bbox: [50, 80, 80, 40], confidence: 0.88 },
      { id: 'r3', text: '时习之', bbox: [50, 130, 120, 40], confidence: 0.91 },
      { id: 'r4', text: '不亦说乎', bbox: [50, 180, 160, 40], confidence: 0.87 },
      { id: 'r5', text: '有朋', bbox: [200, 30, 80, 40], confidence: 0.93 },
      { id: 'r6', text: '自远方来', bbox: [200, 80, 160, 40], confidence: 0.85 },
      { id: 'r7', text: '不亦乐乎', bbox: [200, 130, 160, 40], confidence: 0.92 },
    ],
    annotations: [],
    createdAt: '2025-01-15'
  }

  const VARIANT_DICT: Record<string, string> = {
    '説': '说', '學': '学', '習': '习', '遠': '远', '樂': '乐', '書': '书',
    '國': '国', '東': '东', '長': '长', '門': '门', '馬': '马', '鳥': '鸟',
    '風': '风', '雲': '云', '龍': '龙', '車': '车', '萬': '万', '見': '见',
  }

  function loadMockDocument() {
    documents.value = [MOCK_DOC]
    currentDoc.value = MOCK_DOC
  }

  async function uploadAndOCR(file: File) {
    isLoading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const resp = await fetch('/api/ocr', { method: 'POST', body: formData })
      if (resp.ok) {
        const data = await resp.json()
        const doc: Document = {
          id: Date.now().toString(),
          name: file.name,
          imageUrl: URL.createObjectURL(file),
          results: data.results || [],
          annotations: [],
          createdAt: new Date().toISOString()
        }
        documents.value.push(doc)
        currentDoc.value = doc
      }
    } catch {
      // Use mock data as fallback
      loadMockDocument()
    } finally {
      isLoading.value = false
    }
  }

  function addAnnotation(type: Annotation['type'], bbox: [number, number, number, number], label: string, content: string) {
    if (!currentDoc.value) return
    currentDoc.value.annotations.push({
      id: Date.now().toString(),
      type, bbox, label, content
    })
  }

  function removeAnnotation(id: string) {
    if (!currentDoc.value) return
    currentDoc.value.annotations = currentDoc.value.annotations.filter(a => a.id !== id)
  }

  function convertVariant(text: string): string {
    return text.split('').map(c => VARIANT_DICT[c] || c).join('')
  }

  function searchInDocuments(query: string) {
    const q = query.toLowerCase()
    searchResults.value = documents.value.flatMap(d =>
      d.results.filter(r => r.text.includes(q) || (r.corrected || '').includes(q))
    )
  }

  function addBatchFiles(files: File[]) {
    const items: BatchItem[] = files.map((file, i) => ({
      id: `${Date.now()}_${i}`,
      file,
      status: 'pending' as const,
      progress: 0,
    }))
    batchQueue.value.push(...items)
    if (!isBatchProcessing.value) {
      processBatchQueue()
    }
  }

  async function processBatchQueue() {
    if (isBatchProcessing.value) return
    isBatchProcessing.value = true

    while (true) {
      const next = batchQueue.value.find(b => b.status === 'pending')
      if (!next) break

      next.status = 'processing'
      next.progress = 10

      try {
        const formData = new FormData()
        formData.append('file', next.file)

        next.progress = 30
        const resp = await fetch('/api/ocr', { method: 'POST', body: formData })

        if (resp.ok) {
          next.progress = 80
          const data = await resp.json()
          const doc: Document = {
            id: Date.now().toString() + '_' + next.id,
            name: next.file.name,
            imageUrl: URL.createObjectURL(next.file),
            results: data.results || [],
            annotations: [],
            createdAt: new Date().toISOString()
          }
          documents.value.push(doc)
          next.docId = doc.id
          next.progress = 100
          next.status = 'done'
          if (!currentDoc.value) {
            currentDoc.value = doc
          }
        } else {
          next.status = 'error'
          next.errorMsg = `HTTP ${resp.status}`
          next.progress = 0
        }
      } catch (err) {
        next.status = 'error'
        next.errorMsg = err instanceof Error ? err.message : '未知错误'
        next.progress = 0
      }
    }

    isBatchProcessing.value = false
  }

  function removeBatchItem(id: string) {
    batchQueue.value = batchQueue.value.filter(b => b.id !== id)
  }

  function clearCompletedBatch() {
    batchQueue.value = batchQueue.value.filter(b => b.status !== 'done' && b.status !== 'error')
  }

  function exportTEI(): string {
    if (!currentDoc.value) return ''
    let tei = '<?xml version="1.0" encoding="UTF-8"?>\n'
    tei += '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    tei += `  <teiHeader><fileDesc><titleStmt><title>${currentDoc.value.name}</title></titleStmt></fileDesc></teiHeader>\n`
    tei += '  <text><body>\n'
    for (const r of currentDoc.value.results) {
      tei += `    <seg type="line" xml:id="${r.id}" cert="${r.confidence}">${r.corrected || r.text}</seg>\n`
    }
    tei += '  </body></text>\n</TEI>'
    return tei
  }

  return {
    documents, currentDoc, isLoading, searchQuery, searchResults,
    batchQueue, isBatchProcessing, batchSummary,
    loadMockDocument, uploadAndOCR, addBatchFiles, removeBatchItem, clearCompletedBatch,
    addAnnotation, removeAnnotation,
    convertVariant, searchInDocuments, exportTEI
  }
})

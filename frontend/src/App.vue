<template>
  <div class="flex h-screen">
    <!-- Left: Document list -->
    <div class="w-64 bg-gray-900 p-4 flex flex-col gap-3 border-r border-gray-800">
      <h1 class="text-lg font-bold text-amber-400">古籍 OCR 标注平台</h1>

      <div>
        <label class="block bg-amber-500 text-black text-center py-2 rounded cursor-pointer hover:bg-amber-400 text-sm font-medium">
          上传古籍图片
          <input type="file" accept="image/*" @change="onUpload" class="hidden" />
        </label>
      </div>

      <div>
        <label class="block bg-indigo-500 text-white text-center py-2 rounded cursor-pointer hover:bg-indigo-400 text-sm font-medium">
          批量导入
          <input type="file" accept="image/*" multiple @change="onBatchUpload" class="hidden" />
        </label>
      </div>

      <button @click="store.loadMockDocument()" class="bg-gray-800 py-2 rounded text-sm hover:bg-gray-700">
        加载示例文档
      </button>

      <!-- Search -->
      <div>
        <input v-model="store.searchQuery" @input="store.searchInDocuments(store.searchQuery)"
          placeholder="全文检索..." class="w-full bg-gray-800 rounded px-3 py-2 text-sm" />
        <div v-if="store.searchResults.length" class="mt-1 space-y-1">
          <div v-for="r in store.searchResults" :key="r.id" class="bg-gray-800 rounded p-1 text-xs">
            {{ r.text }} <span class="text-gray-500">{{ (r.confidence * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>

      <!-- Batch Progress Panel -->
      <div v-if="store.batchQueue.length" class="bg-gray-800 rounded p-3 space-y-2">
        <div class="flex justify-between items-center">
          <h3 class="text-amber-300 font-bold text-xs">批量导入进度</h3>
          <button v-if="store.batchSummary && store.batchSummary.done + store.batchSummary.error === store.batchSummary.total"
            @click="store.clearCompletedBatch()" class="text-xs text-gray-400 hover:text-white">清空</button>
        </div>

        <div v-if="store.batchSummary" class="text-xs text-gray-400 flex justify-between">
          <span>总计 {{ store.batchSummary.total }} 份</span>
          <span>总进度 {{ store.batchSummary.overallProgress }}%</span>
        </div>

        <div class="w-full bg-gray-700 rounded-full h-2">
          <div class="h-2 rounded-full transition-all duration-300"
            :style="{ width: (store.batchSummary?.overallProgress || 0) + '%' }"
            :class="store.batchSummary && store.batchSummary.error > 0 ? 'bg-yellow-500' : 'bg-indigo-500'">
          </div>
        </div>

        <div v-if="store.batchSummary" class="flex gap-2 text-xs">
          <span class="text-green-400">完成 {{ store.batchSummary.done }}</span>
          <span class="text-indigo-400">处理中 {{ store.batchSummary.processing }}</span>
          <span class="text-gray-500">等待 {{ store.batchSummary.pending }}</span>
          <span v-if="store.batchSummary.error" class="text-red-400">失败 {{ store.batchSummary.error }}</span>
        </div>

        <div class="max-h-40 overflow-y-auto space-y-1">
          <div v-for="item in store.batchQueue" :key="item.id"
            class="flex items-center gap-2 text-xs py-1 px-2 rounded"
            :class="item.status === 'processing' ? 'bg-indigo-900/30' : item.status === 'done' ? 'bg-green-900/30' : item.status === 'error' ? 'bg-red-900/30' : 'bg-gray-800'">
            <span class="flex-1 truncate" :title="item.file.name">{{ item.file.name }}</span>
            <span v-if="item.status === 'pending'" class="text-gray-500 shrink-0">等待中</span>
            <span v-else-if="item.status === 'processing'" class="text-indigo-400 shrink-0">{{ item.progress }}%</span>
            <span v-else-if="item.status === 'done'" class="text-green-400 shrink-0">✓</span>
            <span v-else-if="item.status === 'error'" class="text-red-400 shrink-0" :title="item.errorMsg">✗</span>
            <button v-if="item.status === 'done' || item.status === 'error'"
              @click="store.removeBatchItem(item.id)" class="text-gray-600 hover:text-white shrink-0">×</button>
          </div>
        </div>
      </div>

      <!-- Document list -->
      <div class="flex-1 overflow-y-auto space-y-1">
        <div v-for="d in store.documents" :key="d.id" @click="store.currentDoc = d"
          class="bg-gray-800 rounded p-2 cursor-pointer text-sm"
          :class="store.currentDoc?.id === d.id ? 'ring-1 ring-amber-500' : ''">
          {{ d.name }}
          <div class="text-xs text-gray-500">{{ d.results.length }} 行识别</div>
        </div>
      </div>

      <!-- Export -->
      <button @click="doExport" class="bg-green-700 py-2 rounded text-sm hover:bg-green-600">
        导出 TEI/XML
      </button>
    </div>

    <!-- Center: Image + OCR overlay -->
    <div class="flex-1 relative bg-gray-950 overflow-hidden">
      <ImageCanvas v-if="store.currentDoc" />
      <div v-else class="flex items-center justify-center h-full text-gray-600">
        请上传古籍图片或加载示例文档
      </div>
    </div>

    <!-- Right: OCR results & annotations -->
    <div class="w-80 bg-gray-900 p-4 flex flex-col gap-3 border-l border-gray-800 overflow-y-auto">
      <h3 class="text-amber-300 font-bold text-sm">OCR 识别结果</h3>
      <div v-if="store.currentDoc" class="space-y-2">
        <div v-for="r in store.currentDoc.results" :key="r.id"
          class="bg-gray-800 rounded p-2 text-sm">
          <div class="flex justify-between">
            <span class="text-white font-medium">{{ r.text }}</span>
            <span class="text-xs px-2 py-0.5 rounded"
              :class="r.confidence > 0.9 ? 'bg-green-900 text-green-400' : 'bg-yellow-900 text-yellow-400'">
              {{ (r.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="text-xs text-gray-400 mt-1">
            简体: {{ store.convertVariant(r.text) }}
          </div>
          <input v-model="r.corrected" placeholder="人工校正..."
            class="w-full bg-gray-700 rounded px-2 py-1 text-xs mt-1" />
        </div>
      </div>

      <h3 class="text-amber-300 font-bold text-sm mt-4">标注列表</h3>
      <div v-if="store.currentDoc" class="space-y-1">
        <div v-for="a in store.currentDoc.annotations" :key="a.id"
          class="bg-gray-800 rounded p-2 text-xs flex justify-between">
          <span>[{{ a.type }}] {{ a.label }}: {{ a.content }}</span>
          <button @click="store.removeAnnotation(a.id)" class="text-red-400 hover:underline">删除</button>
        </div>
        <div v-if="!store.currentDoc.annotations.length" class="text-gray-600 text-xs">
          在图片上拖拽框选区域添加标注
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useOcrStore } from './store/ocr'
import ImageCanvas from './components/ImageCanvas.vue'

const store = useOcrStore()

function onUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) store.uploadAndOCR(file)
}

function onBatchUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) {
    store.addBatchFiles(Array.from(files))
  }
  ;(e.target as HTMLInputElement).value = ''
}

function doExport() {
  const tei = store.exportTEI()
  if (!tei) return
  const blob = new Blob([tei], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentDoc?.name || 'export'}.xml`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

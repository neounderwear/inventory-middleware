<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { formatWIB, fetchTimestamps, type SyncTimestamps } from '../utils/api'

const API = ''

const masterFile = ref<File | null>(null)
const gpdFile = ref<File | null>(null)
const rjmFile = ref<File | null>(null)
const sevenbFile = ref<File | null>(null)
const jagoanFile = ref<File | null>(null)

const isUploading = ref<Record<string, boolean>>({})
const uploadMessage = ref<Record<string, string>>({})
const isSuccess = ref<Record<string, boolean>>({})
const timestamps = ref<SyncTimestamps | null>(null)

const loadTimestamps = async () => {
  timestamps.value = await fetchTimestamps()
}

onMounted(loadTimestamps)

const handleFile = (e: Event, type: string) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    if (type === 'master') masterFile.value = target.files[0]
    if (type === 'gpd') gpdFile.value = target.files[0]
    if (type === 'rjm') rjmFile.value = target.files[0]
    if (type === '7b') sevenbFile.value = target.files[0]
    if (type === 'jagoan') jagoanFile.value = target.files[0]
  }
}

const uploadData = async (type: string, file: File | null, endpoint: string) => {
  if (!file) {
    uploadMessage.value[type] = 'Silakan pilih file terlebih dahulu.'
    isSuccess.value[type] = false
    return
  }

  isUploading.value[type] = true
  uploadMessage.value[type] = ''
  isSuccess.value[type] = false

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch(`${API}${endpoint}`, {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      throw new Error(errData?.detail || `Upload failed: ${res.statusText}`)
    }

    const data = await res.json()
    isSuccess.value[type] = true
    uploadMessage.value[type] = `${data.message} (Inserted/Updated: ${data.inserted || data.updated || 0})`
    await loadTimestamps()
  } catch (err: any) {
    isSuccess.value[type] = false
    uploadMessage.value[type] = err.message || 'An error occurred during upload'
  } finally {
    isUploading.value[type] = false
  }
}
</script>

<template>
  <main class="p-8 max-w-5xl mx-auto space-y-8">
    <div class="mb-8">
      <h1 class="text-4xl font-black uppercase tracking-tight border-black border-[3px] bg-white p-4 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] inline-block">
        📥 DATA CENTER
      </h1>
    </div>

    <!-- Master Data -->
    <section class="card-brutal bg-violet-300">
      <h2 class="text-2xl font-black mb-2 uppercase">⚙️ Master Data</h2>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_master_sync) }}</p>
      <div class="flex flex-col md:flex-row gap-4 items-end">
        <div class="flex flex-col flex-1">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File master_data_v2.xlsx</label>
          <input type="file" accept=".xlsx" @change="e => handleFile(e, 'master')" class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none" />
        </div>
        <button @click="uploadData('master', masterFile, '/api/master/upload')" :disabled="isUploading['master']" class="btn-brutal bg-white px-8 py-3">
          {{ isUploading['master'] ? 'UPLOADING...' : 'UPLOAD' }}
        </button>
      </div>
      <div v-if="uploadMessage['master']" class="mt-4 border-black border-[3px] p-2 font-bold bg-white">{{ uploadMessage['master'] }}</div>
    </section>

    <!-- Stok GPD -->
    <section class="card-brutal bg-cyan-300">
      <h2 class="text-2xl font-black mb-2 uppercase">🏭 Sisa Stok GPD</h2>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_gpd_sync) }}</p>
      <div class="flex flex-col md:flex-row gap-4 items-end">
        <div class="flex flex-col flex-1">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File sisa_stok_gpd.xlsx</label>
          <input type="file" accept=".xlsx" @change="e => handleFile(e, 'gpd')" class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none" />
        </div>
        <button @click="uploadData('gpd', gpdFile, '/api/master/sync-stock/GPD')" :disabled="isUploading['gpd']" class="btn-brutal bg-white px-8 py-3">
          {{ isUploading['gpd'] ? 'UPLOADING...' : 'UPLOAD' }}
        </button>
      </div>
      <div v-if="uploadMessage['gpd']" class="mt-4 border-black border-[3px] p-2 font-bold bg-white">{{ uploadMessage['gpd'] }}</div>
    </section>

    <!-- Stok RJM -->
    <section class="card-brutal bg-yellow-300">
      <h2 class="text-2xl font-black mb-2 uppercase">🏪 Sisa Stok RJM</h2>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_rjm_sync) }}</p>
      <div class="flex flex-col md:flex-row gap-4 items-end">
        <div class="flex flex-col flex-1">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File sisa_stok_rjm.xlsx</label>
          <input type="file" accept=".xlsx" @change="e => handleFile(e, 'rjm')" class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none" />
        </div>
        <button @click="uploadData('rjm', rjmFile, '/api/master/sync-stock/RJM')" :disabled="isUploading['rjm']" class="btn-brutal bg-white px-8 py-3">
          {{ isUploading['rjm'] ? 'UPLOADING...' : 'UPLOAD' }}
        </button>
      </div>
      <div v-if="uploadMessage['rjm']" class="mt-4 border-black border-[3px] p-2 font-bold bg-white">{{ uploadMessage['rjm'] }}</div>
    </section>

    <!-- Stok 7B -->
    <section class="card-brutal bg-pink-300">
      <h2 class="text-2xl font-black mb-2 uppercase">🏪 Sisa Stok 7B</h2>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_7b_sync) }}</p>
      <div class="flex flex-col md:flex-row gap-4 items-end">
        <div class="flex flex-col flex-1">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File sisa_stok_7b.xlsx</label>
          <input type="file" accept=".xlsx" @change="e => handleFile(e, '7b')" class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none" />
        </div>
        <button @click="uploadData('7b', sevenbFile, '/api/master/sync-stock/7B')" :disabled="isUploading['7b']" class="btn-brutal bg-white px-8 py-3">
          {{ isUploading['7b'] ? 'UPLOADING...' : 'UPLOAD' }}
        </button>
      </div>
      <div v-if="uploadMessage['7b']" class="mt-4 border-black border-[3px] p-2 font-bold bg-white">{{ uploadMessage['7b'] }}</div>
    </section>

    <!-- Stok JAGOAN -->
    <section class="card-brutal bg-green-300">
      <h2 class="text-2xl font-black mb-2 uppercase">🏪 Sisa Stok JAGOAN</h2>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_jagoan_sync) }}</p>
      <div class="flex flex-col md:flex-row gap-4 items-end">
        <div class="flex flex-col flex-1">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File sisa_stok_jg.xlsx</label>
          <input type="file" accept=".xlsx" @change="e => handleFile(e, 'jagoan')" class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none" />
        </div>
        <button @click="uploadData('jagoan', jagoanFile, '/api/master/sync-stock/JAGOAN')" :disabled="isUploading['jagoan']" class="btn-brutal bg-white px-8 py-3">
          {{ isUploading['jagoan'] ? 'UPLOADING...' : 'UPLOAD' }}
        </button>
      </div>
      <div v-if="uploadMessage['jagoan']" class="mt-4 border-black border-[3px] p-2 font-bold bg-white">{{ uploadMessage['jagoan'] }}</div>
    </section>

  </main>
</template>

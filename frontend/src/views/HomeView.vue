<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { formatWIB, fetchTimestamps, type SyncTimestamps } from '../utils/api'

const API = ''

const masterFile = ref<File | null>(null)
const isUploading = ref(false)
const uploadMessage = ref('')
const isSuccess = ref(false)
const timestamps = ref<SyncTimestamps | null>(null)

const loadTimestamps = async () => {
  timestamps.value = await fetchTimestamps()
}

onMounted(loadTimestamps)

const handleFile = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    masterFile.value = target.files[0]
  }
}

const uploadMasterData = async () => {
  if (!masterFile.value) {
    uploadMessage.value = 'Silakan pilih file master_data_v2.xlsx terlebih dahulu.'
    isSuccess.value = false
    return
  }

  isUploading.value = true
  uploadMessage.value = ''
  isSuccess.value = false

  const formData = new FormData()
  formData.append('file', masterFile.value)

  try {
    const res = await fetch(`${API}/api/master/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      throw new Error(errData?.detail || `Upload failed: ${res.statusText}`)
    }

    const data = await res.json()
    isSuccess.value = true
    uploadMessage.value = `${data.message} (Inserted: ${data.inserted ?? 0}, Updated: ${data.updated ?? 0})`
    await loadTimestamps()
  } catch (err: any) {
    isSuccess.value = false
    uploadMessage.value = err.message || 'An error occurred during upload'
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <main class="p-8 max-w-5xl mx-auto space-y-12">
    <div class="mb-12 text-center">
      <h1 class="text-4xl md:text-5xl font-black mb-4 uppercase tracking-tighter">Inventory Middleware</h1>
      <p class="text-xl font-bold inline-block">
        <span class="bg-black text-white px-2 py-1">Sistem Manajemen Stok dan Purchase Order</span>
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <router-link to="/toko" class="card-brutal bg-yellow-300 text-black no-underline block hover:-translate-y-1 transition-transform">
        <h2 class="uppercase font-black text-2xl mb-2">📦 PO Toko</h2>
        <p class="font-semibold text-lg">Kelola Purchase Order dari Toko</p>
      </router-link>

      <router-link to="/gudang" class="card-brutal bg-cyan-300 text-black no-underline block hover:-translate-y-1 transition-transform">
        <h2 class="uppercase font-black text-2xl mb-2">🏭 Fullfillment Gudang</h2>
        <p class="font-semibold text-lg">Ambil dan input barang</p>
      </router-link>

      <router-link to="/update-stock" class="card-brutal bg-pink-300 text-black no-underline block hover:-translate-y-1 transition-transform">
        <h2 class="uppercase font-black text-2xl mb-2">📊 Update Stock</h2>
        <p class="font-semibold text-lg">Generate laporan stok</p>
      </router-link>
    </div>

    <section class="card-brutal bg-gray-50 border-[3px] border-black p-6 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
      <h2 class="text-3xl font-black mb-4 uppercase">⚙️ Master Data Management</h2>
      <p class="font-semibold mb-6">Upload <span class="bg-black text-white px-1">master_data_v2.xlsx</span> untuk memperbarui database SKU, Nama Produk, Kategori, Brand, dan Buffer Stock.</p>
      <p class="text-sm font-mono mb-4 bg-black text-white px-2 py-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_master_sync) }}</p>
      
      <div class="flex flex-col md:flex-row gap-4 items-start md:items-end">
        <div class="flex flex-col flex-1 w-full">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File Master Data (.xlsx)</label>
          <input 
            type="file" 
            accept=".xlsx" 
            @change="handleFile" 
            class="border-black border-[3px] p-2 bg-white w-full cursor-pointer focus:outline-none"
          />
        </div>
        
        <button 
          @click="uploadMasterData" 
          :disabled="isUploading || !masterFile"
          class="btn-brutal bg-violet-300 px-8 py-3 h-[52px] whitespace-nowrap"
          :class="{ 'opacity-50 cursor-not-allowed': isUploading || !masterFile }"
        >
          {{ isUploading ? 'UPLOADING...' : 'UPLOAD MASTER DATA' }}
        </button>
      </div>

      <div 
        v-if="uploadMessage" 
        class="mt-6 border-black border-[3px] p-4 font-bold"
        :class="isSuccess ? 'bg-green-300' : 'bg-pink-300'"
      >
        {{ uploadMessage }}
      </div>
    </section>
  </main>
</template>

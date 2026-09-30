<template>
  <div class="min-h-screen bg-white p-4 max-w-md mx-auto flex flex-col gap-6">
    <!-- Sync Warehouse Stock Section -->
    <div v-if="!store.currentPO" class="flex flex-col gap-4">
      <div class="card-brutal bg-yellow-100">
        <h2 class="text-xl font-black mb-3 uppercase tracking-wider">📦 Sync Stok Gudang</h2>
        <p class="text-sm font-bold mb-3">Upload file stok gudang (sisa_stok_gpd.xlsx) untuk sinkronisasi ke database.</p>
        <input 
          type="file" 
          accept=".xlsx" 
          @change="handleSyncFile" 
          class="border-black border-[3px] p-2 bg-white w-full mb-3"
        />
        
        <p class="text-xs font-bold mb-1 uppercase tracking-wider">FILE STOK RJM (.XLSX) - KHUSUS CROCODILE & GTMAN (OPSIONAL)</p>
        <input 
          type="file" 
          accept=".xlsx" 
          @change="handleRjmFile" 
          class="border-black border-[3px] p-2 bg-white w-full mb-3"
        />
        <div v-if="syncError" class="bg-pink-300 border-black border-[3px] p-2 font-bold text-sm mb-3">
          {{ syncError }}
        </div>
        <div v-if="syncSuccess" class="bg-green-300 border-black border-[3px] p-2 font-bold text-sm mb-3">
          {{ syncSuccess }}
        </div>
        <button 
          @click="syncGudangStock" 
          :disabled="isSyncing || !syncFile"
          class="btn-brutal bg-cyan-300 w-full"
          :class="{ 'opacity-50 cursor-not-allowed': isSyncing || !syncFile }"
        >
          {{ isSyncing ? 'SYNCING...' : 'SYNC STOCK GUDANG' }}
        </button>
      </div>
    </div>

    <!-- State 1: PO Selection -->
    <div v-if="!store.currentPO" class="flex flex-col gap-4">
      <h1 class="text-3xl font-black mb-4 uppercase">🏭 Gudang Fulfillment</h1>
      <div v-if="store.isLoading" class="text-xl font-bold">Loading...</div>
      <template v-else>
        <div v-if="store.availablePOs.length === 0" class="text-lg font-bold border-black border-[3px] p-4 bg-yellow-300 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          Tidak ada PO yang siap diproses
        </div>
        <div 
          v-for="po in store.availablePOs" 
          :key="po.id" 
          class="card-brutal"
        >
          <div class="flex justify-between items-start mb-1">
            <div class="font-black text-xl">{{ po.nomor_po }}</div>
            <div v-if="po.status === 'COMPLETED_BY_GUDANG'" class="bg-green-400 border-black border-[2px] px-2 py-0.5 text-xs font-black uppercase tracking-wider">
              COMPLETED
            </div>
            <div v-else class="bg-yellow-300 border-black border-[2px] px-2 py-0.5 text-xs font-black uppercase tracking-wider">
              CONFIRMED
            </div>
          </div>
          <div class="text-lg">{{ po.entitas_toko }}</div>
          <div class="text-sm font-bold mt-2 bg-black text-white px-2 py-1 inline-block">
            {{ po.items?.length || po.item_count || 0 }} ITEMS
          </div>
          <div class="mt-3">
            <!-- Completed PO: show download button -->
            <a 
              v-if="po.status === 'COMPLETED_BY_GUDANG'"
              :href="`${API}/api/export/olsera/${po.id}`"
              target="_blank"
              class="btn-brutal bg-pink-300 w-full text-center flex items-center justify-center no-underline text-black"
            >
              📥 DOWNLOAD OLSERA FILES
            </a>
            <!-- Confirmed PO: show process button -->
            <button 
              v-else
              @click="handleSelectPO(po.id)"
              class="btn-brutal bg-cyan-300 w-full"
            >
              ▶ PROCESS
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- State 2: Game Mode -->
    <div v-else-if="store.currentPO && !store.isCompleted" class="flex flex-col h-full flex-grow relative">
      <!-- Nomor PO prominently at top -->
      <div class="bg-black text-white p-3 mb-4 border-[3px] border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,0.3)]">
        <div class="text-center font-black text-2xl tracking-widest uppercase">{{ store.currentPO.nomor_po }}</div>
        <div class="text-center text-sm font-bold opacity-80">{{ store.currentPO.entitas_toko }}</div>
      </div>

      <div class="mb-4">
        <div class="flex justify-between items-end mb-2">
          <div class="font-black text-xl">Item {{ store.progress }}</div>
          <button @click="store.reset()" class="text-sm font-bold underline">Batal</button>
        </div>
        <div class="w-full h-4 bg-gray-200 border-black border-brutal relative shadow-brutal-sm">
          <div 
            class="h-full bg-yellow-300"
            :style="{ width: `${((store.currentIndex) / store.totalItems) * 100}%` }"
          ></div>
        </div>
      </div>
      
      <div v-if="store.currentItem" class="flex flex-col gap-4">
        <div class="card-brutal flex flex-col gap-2">
          <div>
            <h2 class="text-2xl font-black mb-1 leading-tight">{{ store.currentItem.nama_produk }}</h2>
            <div class="text-gray-500 font-bold font-mono">{{ store.currentItem.sku }}</div>
          </div>
          <div class="text-4xl font-black text-center py-3 border-y-4 border-black border-dashed uppercase">
            <span class="tracking-wider">Diminta:</span> {{ store.currentItem.qty_request }}
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-bold text-lg text-center uppercase tracking-wider">Fulfill Qty:</label>
            <input 
              type="number" 
              v-model="manualQty" 
              class="border-[3px] border-black p-2 text-center text-6xl font-black w-full shadow-brutal-sm outline-none focus:bg-yellow-50"
              min="0"
            />
          </div>
        </div>

        <div class="flex flex-col gap-3">
          <button 
            @click="handleSaveAndNext" 
            class="btn-brutal bg-green-400 min-h-20 text-2xl"
          >
            🟢 SIMPAN & LANJUT
          </button>
          <button 
            @click="store.markEmpty()" 
            class="btn-brutal bg-red-400 min-h-20 text-2xl"
          >
            🔴 KOSONG
          </button>
        </div>
      </div>
    </div>

    <!-- State 3: Summary -->
    <div v-else-if="store.isCompleted" class="flex flex-col gap-6 pb-8">
      <h1 class="text-3xl font-black uppercase">📋 Rekap Fulfillment</h1>

      <div class="card-brutal bg-green-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">✅ FULFILLED ({{ store.fulfilledItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.fulfilledItems" :key="item.id">
            {{ item.nama_produk }} ({{ item.qty_fulfilled }})
          </li>
        </ul>
      </div>

      <div class="card-brutal bg-yellow-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">⚠️ PARTIAL ({{ store.partialItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.partialItems" :key="item.id">
            {{ item.nama_produk }} ({{ item.qty_fulfilled }}/{{ item.qty_request }})
          </li>
        </ul>
      </div>

      <div class="card-brutal bg-red-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">❌ KOSONG ({{ store.emptyItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.emptyItems" :key="item.id">
            {{ item.nama_produk }}
          </li>
        </ul>
      </div>

      <button 
        v-if="!isSubmitted"
        @click="handleSubmit" 
        class="btn-brutal bg-cyan-300 min-h-16 text-2xl mt-4 flex justify-center items-center"
        :disabled="store.isLoading"
      >
        <span v-if="store.isLoading">PROCESSING...</span>
        <span v-else>SUBMIT FULFILLMENT</span>
      </button>

      <div v-else class="flex flex-col gap-4 mt-4">
        <a 
          :href="`${API}/api/export/olsera/${store.currentPO?.id}`"
          target="_blank"
          class="btn-brutal bg-pink-300 min-h-16 text-xl text-center flex items-center justify-center no-underline text-black"
        >
          📥 DOWNLOAD OLSERA FILES
        </a>
        <button 
          @click="handleBack" 
          class="btn-brutal bg-white min-h-12 text-lg"
        >
          KEMBALI
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useFulfillmentStore } from '../stores/fulfillmentStore'

const API = import.meta.env.VITE_API_URL || 'https://inventory.underwear.my.id'
const store = useFulfillmentStore()
const manualQty = ref(0)
const isSubmitted = ref(false)

// Sync warehouse stock state
const syncFile = ref<File | null>(null)
const fileRjm = ref<File | null>(null)
const isSyncing = ref(false)
const syncError = ref('')
const syncSuccess = ref('')

const handleSyncFile = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    syncFile.value = target.files[0]
    syncError.value = ''
    syncSuccess.value = ''
  }
}

const handleRjmFile = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    fileRjm.value = target.files[0]
  }
}

const syncGudangStock = async () => {
  if (!syncFile.value) return
  
  isSyncing.value = true
  syncError.value = ''
  syncSuccess.value = ''

  const formData = new FormData()
  formData.append('file', syncFile.value)
  if (fileRjm.value) {
    formData.append('file_rjm', fileRjm.value)
  }

  try {
    const res = await fetch(`${API}/api/master/sync-gudang-stock`, {
      method: 'POST',
      body: formData
    })
    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      throw new Error(errData?.detail || 'Sync failed')
    }
    const data = await res.json()
    syncSuccess.value = `${data.message} (Updated: ${data.updated}, Not Found: ${data.not_found})`
  } catch (err: any) {
    syncError.value = err.message || 'Failed to sync stock'
  } finally {
    isSyncing.value = false
  }
}

onMounted(() => {
  store.fetchConfirmedPOs()
})

watch(() => store.currentItem, (newItem) => {
  if (newItem) {
    manualQty.value = newItem.qty_request
  }
}, { immediate: true })

const handleSelectPO = (id: string) => {
  isSubmitted.value = false
  store.selectPO(id)
}

const handleSaveAndNext = () => {
  store.saveAndNext(Number(manualQty.value))
}

const handleSubmit = async () => {
  await store.submitFulfillment()
  isSubmitted.value = true
}

const handleBack = () => {
  isSubmitted.value = false
  store.reset()
  store.fetchConfirmedPOs()
}
</script>

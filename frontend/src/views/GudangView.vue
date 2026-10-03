<template>
  <div class="min-h-screen bg-white p-4 max-w-md mx-auto flex flex-col gap-6">
    <!-- Sync Warehouse Stock Section -->
    <div v-if="!store.currentPO" class="flex flex-col gap-4">
      <div class="card-brutal bg-yellow-100">
        <h2 class="text-xl font-black mb-3 uppercase tracking-wider">📦 Sync Stok Gudang</h2>
        <p class="text-sm font-bold mb-3">Upload file stok gudang (sisa_stok_gpd.xlsx) untuk sinkronisasi ke database.</p>

        <p class="text-xs font-bold mb-1 uppercase tracking-wider">FILE STOK GPD (.XLSX) - WAJIB</p>
        <p class="text-xs font-mono mb-1 bg-black text-white px-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_gpd_sync) }}</p>
        <input 
          type="file" 
          accept=".xlsx" 
          @change="handleSyncFile" 
          class="border-black border-[3px] p-2 bg-white w-full mb-3"
        />
        
        <p class="text-xs font-bold mb-1 uppercase tracking-wider">FILE STOK RJM (.XLSX) - KHUSUS CROCODILE &amp; GTMAN (OPSIONAL)</p>
        <p class="text-xs font-mono mb-1 bg-black text-white px-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_rjm_sync) }}</p>
        <input 
          type="file" 
          accept=".xlsx" 
          @change="handleRjmFile" 
          class="border-black border-[3px] p-2 bg-white w-full mb-3"
        />

        <p class="text-xs font-bold mb-1 uppercase tracking-wider">FILE STOK 7B (.XLSX) - EKSKLUSIF (OPSIONAL)</p>
        <p class="text-xs font-mono mb-1 bg-black text-white px-1 inline-block">Last Updated: {{ formatWIB(timestamps?.last_7b_sync) }}</p>
        <input 
          type="file" 
          accept=".xlsx" 
          @change="handle7bFile" 
          class="border-black border-[3px] p-2 bg-white w-full mb-3"
        />

        <div v-if="syncError" class="bg-pink-300 border-black border-[3px] p-2 font-bold text-sm mb-3">
          {{ syncError }}
        </div>
        <div v-if="syncSuccess" class="bg-green-300 border-black border-[3px] p-2 font-bold text-sm mb-3">
          {{ syncSuccess }}
        </div>
        <div v-for="w in syncWarnings" :key="w" class="bg-yellow-300 border-black border-[3px] p-2 font-bold text-sm mb-3">
          ⚠️ {{ w }}
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
            <div v-else-if="store.savedProgressIds.includes(po.id)" class="bg-orange-300 border-black border-[2px] px-2 py-0.5 text-xs font-black uppercase tracking-wider">
              IN PROGRESS
            </div>
            <div v-else class="bg-yellow-300 border-black border-[2px] px-2 py-0.5 text-xs font-black uppercase tracking-wider">
              CONFIRMED
            </div>
          </div>
          <div class="text-lg">{{ po.entitas_toko }}</div>
          <div class="text-sm font-bold">Tujuan: {{ po.tujuan_po || 'CV GPD' }}</div>
          <div class="text-sm font-bold mt-2 bg-black text-white px-2 py-1 inline-block">
            {{ po.items?.length || po.item_count || 0 }} ITEMS
          </div>
          <div class="mt-3">
            <button 
              @click="handleSelectPO(po)"
              class="btn-brutal w-full"
              :class="po.status === 'COMPLETED_BY_GUDANG' ? 'bg-green-300' : 'bg-cyan-300'"
            >
              <template v-if="po.status === 'COMPLETED_BY_GUDANG'">📋 PROCESS (LIHAT REKAP)</template>
              <template v-else-if="store.savedProgressIds.includes(po.id)">▶ LANJUTKAN PROSES</template>
              <template v-else>▶ PROCESS</template>
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
        <div class="text-center text-sm font-bold opacity-80">{{ store.currentPO.entitas_toko }} → {{ store.currentPO.tujuan_po || 'CV GPD' }}</div>
      </div>

      <div class="mb-4">
        <div class="flex justify-between items-end mb-2">
          <div class="font-black text-xl">Selesai {{ store.progress }}</div>
          <div class="flex gap-3 items-center">
            <button @click="showRecap = true" class="text-sm font-black underline">📋 Progress</button>
            <button @click="store.reset()" class="text-sm font-bold underline">Keluar</button>
          </div>
        </div>
        <div class="w-full h-4 bg-gray-200 border-black border-brutal relative shadow-brutal-sm">
          <div 
            class="h-full bg-yellow-300"
            :style="{ width: `${store.progressPercent}%` }"
          ></div>
        </div>
        <p class="text-xs font-bold mt-1 opacity-70">Progress tersimpan otomatis — aman untuk keluar dan lanjut nanti.</p>
      </div>
      
      <div v-if="store.currentItem" class="flex flex-col gap-4">
        <div class="card-brutal flex flex-col gap-2">
          <div>
            <div class="flex gap-2 mb-1 flex-wrap">
              <span v-if="store.currentItem.brand" class="bg-black text-white text-xs font-black px-2 py-0.5 uppercase">{{ store.currentItem.brand }}</span>
              <span v-if="store.skippedIds.includes(store.currentItem.id)" class="bg-orange-300 border-black border-[2px] text-xs font-black px-2 py-0.5 uppercase">DILEWATI SEBELUMNYA</span>
            </div>
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
            🟢 SIMPAN &amp; LANJUT
          </button>
          <button 
            @click="store.markEmpty()" 
            class="btn-brutal bg-red-400 min-h-20 text-2xl"
          >
            🔴 KOSONG
          </button>
          <button 
            @click="store.skipCurrent()" 
            :disabled="store.queue.length < 2"
            class="btn-brutal bg-orange-200 min-h-14 text-xl"
            :class="{ 'opacity-50 cursor-not-allowed': store.queue.length < 2 }"
          >
            ⏭️ LEWATI SEMENTARA
          </button>
        </div>
      </div>
    </div>

    <!-- State 3: Summary -->
    <div v-else-if="store.isCompleted" class="flex flex-col gap-6 pb-8">
      <h1 class="text-3xl font-black uppercase">📋 Rekap Fulfillment</h1>
      <div class="text-sm font-bold">{{ store.currentPO?.nomor_po }} → {{ store.currentPO?.tujuan_po || 'CV GPD' }}</div>

      <div class="card-brutal bg-green-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">✅ FULFILLED ({{ store.fulfilledItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.fulfilledItems" :key="item.id">
            {{ item.nama_produk }} ({{ item.qty_fulfilled }})
            <button v-if="!isSubmitted" @click="store.jumpTo(item.id)" class="text-xs underline ml-1">ubah</button>
          </li>
        </ul>
      </div>

      <div class="card-brutal bg-yellow-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">⚠️ PARTIAL ({{ store.partialItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.partialItems" :key="item.id">
            {{ item.nama_produk }} ({{ item.qty_fulfilled }}/{{ item.qty_request }})
            <button v-if="!isSubmitted" @click="store.jumpTo(item.id)" class="text-xs underline ml-1">ubah</button>
          </li>
        </ul>
      </div>

      <div class="card-brutal bg-red-200">
        <h2 class="text-xl font-black mb-2 uppercase tracking-wider">❌ KOSONG ({{ store.emptyItems.length }})</h2>
        <ul class="list-disc pl-5 font-bold space-y-1">
          <li v-for="item in store.emptyItems" :key="item.id">
            {{ item.nama_produk }}
            <button v-if="!isSubmitted" @click="store.jumpTo(item.id)" class="text-xs underline ml-1">ubah</button>
          </li>
        </ul>
      </div>

      <div v-if="submitError" class="bg-pink-300 border-black border-[3px] p-2 font-bold text-sm">
        {{ submitError }}
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
        <button 
          @click="downloadPenjualan(store.currentPO!)"
          class="btn-brutal bg-green-300 min-h-16 text-xl text-center flex items-center justify-center text-black"
        >
          📥 DOWNLOAD PENJUALAN (CSV)
        </button>
        <button 
          @click="downloadPembelian(store.currentPO!)"
          class="btn-brutal bg-blue-300 min-h-16 text-xl text-center flex items-center justify-center text-black"
        >
          📥 DOWNLOAD PEMBELIAN (CSV)
        </button>
        <button 
          @click="handleBack" 
          class="btn-brutal bg-white min-h-12 text-lg"
        >
          KEMBALI
        </button>
      </div>
    </div>

    <!-- Live Progress Drawer (during scanning) -->
    <div v-if="showRecap && store.currentPO" class="fixed inset-0 z-50 flex justify-end bg-black/50" @click.self="showRecap = false">
      <div class="w-full max-w-md h-full bg-white border-l-[4px] border-black p-4 overflow-y-auto flex flex-col gap-4">
        <div class="flex justify-between items-center">
          <h2 class="text-2xl font-black uppercase">📋 Fulfillment Progress</h2>
          <button @click="showRecap = false" class="btn-brutal bg-white px-3 py-1">✕</button>
        </div>
        <div class="font-bold">{{ store.currentPO.nomor_po }} — Selesai {{ store.progress }}</div>

        <div class="card-brutal bg-yellow-100">
          <h3 class="text-lg font-black mb-2 uppercase">⏳ Pending ({{ store.pendingItems.length }})</h3>
          <p v-if="store.pendingItems.length === 0" class="text-sm font-bold opacity-70">Semua item sudah diproses.</p>
          <ul class="flex flex-col gap-1">
            <li v-for="(item, idx) in store.pendingItems" :key="item.id" class="flex justify-between items-center gap-2 border-b-2 border-black/10 py-1">
              <span class="font-bold text-sm">
                <span v-if="idx === 0" class="bg-black text-white text-xs px-1 mr-1">SEKARANG</span>
                <span v-if="store.skippedIds.includes(item.id)" class="bg-orange-300 text-xs px-1 mr-1 border border-black">DILEWATI</span>
                {{ item.nama_produk }} <span class="opacity-60">×{{ item.qty_request }}</span>
              </span>
              <button v-if="idx !== 0" @click="handleJump(item.id)" class="text-xs font-black underline shrink-0">PROSES</button>
            </li>
          </ul>
        </div>

        <div class="card-brutal bg-green-100">
          <h3 class="text-lg font-black mb-2 uppercase">✅ Done ({{ store.doneItems.length }})</h3>
          <p v-if="store.doneItems.length === 0" class="text-sm font-bold opacity-70">Belum ada item yang diproses.</p>
          <ul class="flex flex-col gap-1">
            <li v-for="item in store.doneItems" :key="item.id" class="flex justify-between items-center gap-2 border-b-2 border-black/10 py-1">
              <span class="font-bold text-sm">
                {{ item.nama_produk }}
                <span :class="item.qty_fulfilled === 0 ? 'text-red-600' : item.qty_fulfilled < item.qty_request ? 'text-yellow-700' : 'text-green-700'">
                  ({{ item.qty_fulfilled }}/{{ item.qty_request }})
                </span>
              </span>
              <button @click="handleJump(item.id)" class="text-xs font-black underline shrink-0">UBAH</button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Read-Only Recap Modal (completed POs) -->
    <div v-if="store.recapPO || store.isRecapLoading" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="store.closeRecap()">
      <div class="w-full max-w-md max-h-[90vh] overflow-y-auto bg-white border-[4px] border-black shadow-[8px_8px_0_0_rgba(0,0,0,1)] p-4 flex flex-col gap-4">
        <div v-if="store.isRecapLoading" class="text-xl font-bold">Loading...</div>
        <template v-else-if="store.recapPO">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-2xl font-black uppercase">📋 Rekap (Read-Only)</h2>
              <div class="font-bold">{{ store.recapPO.nomor_po }}</div>
              <div class="text-sm font-bold opacity-80">{{ store.recapPO.entitas_toko }} → {{ store.recapPO.tujuan_po || 'CV GPD' }}</div>
            </div>
            <button @click="store.closeRecap()" class="btn-brutal bg-white px-3 py-1">✕</button>
          </div>

          <div class="card-brutal bg-green-200">
            <h3 class="text-lg font-black mb-2 uppercase">✅ Fulfilled ({{ recapGroups.fulfilled.length }})</h3>
            <ul class="list-disc pl-5 font-bold text-sm space-y-1">
              <li v-for="item in recapGroups.fulfilled" :key="item.id">{{ item.nama_produk }} ({{ item.qty_fulfilled }})</li>
            </ul>
          </div>
          <div class="card-brutal bg-yellow-200">
            <h3 class="text-lg font-black mb-2 uppercase">⚠️ Partial ({{ recapGroups.partial.length }})</h3>
            <ul class="list-disc pl-5 font-bold text-sm space-y-1">
              <li v-for="item in recapGroups.partial" :key="item.id">{{ item.nama_produk }} ({{ item.qty_fulfilled }}/{{ item.qty_request }})</li>
            </ul>
          </div>
          <div class="card-brutal bg-red-200">
            <h3 class="text-lg font-black mb-2 uppercase">❌ Kosong ({{ recapGroups.empty.length }})</h3>
            <ul class="list-disc pl-5 font-bold text-sm space-y-1">
              <li v-for="item in recapGroups.empty" :key="item.id">{{ item.nama_produk }}</li>
            </ul>
          </div>

          <button 
            @click="downloadPenjualan(store.recapPO)"
            class="btn-brutal bg-green-300 min-h-14 text-lg text-center flex items-center justify-center text-black"
          >
            📥 DOWNLOAD PENJUALAN (CSV)
          </button>
          <button 
            @click="downloadPembelian(store.recapPO)"
            class="btn-brutal bg-blue-300 min-h-14 text-lg text-center flex items-center justify-center text-black"
          >
            📥 DOWNLOAD PEMBELIAN (CSV)
          </button>
          <button @click="store.closeRecap()" class="btn-brutal bg-white min-h-12 text-lg">TUTUP</button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFulfillmentStore, type PO } from '../stores/fulfillmentStore'
import { formatWIB, fetchTimestamps, downloadFile, type SyncTimestamps } from '../utils/api'

const API = ''
const store = useFulfillmentStore()
const manualQty = ref(0)
const isSubmitted = ref(false)
const submitError = ref('')
const showRecap = ref(false)
const timestamps = ref<SyncTimestamps | null>(null)

// Sync warehouse stock state
const syncFile = ref<File | null>(null)
const fileRjm = ref<File | null>(null)
const file7b = ref<File | null>(null)
const isSyncing = ref(false)
const syncError = ref('')
const syncSuccess = ref('')
const syncWarnings = ref<string[]>([])

const loadTimestamps = async () => {
  timestamps.value = await fetchTimestamps()
}

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

const handle7bFile = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    file7b.value = target.files[0]
  }
}

const syncGudangStock = async () => {
  if (!syncFile.value) return
  
  isSyncing.value = true
  syncError.value = ''
  syncSuccess.value = ''
  syncWarnings.value = []

  const formData = new FormData()
  formData.append('file', syncFile.value)
  if (fileRjm.value) {
    formData.append('file_rjm', fileRjm.value)
  }
  if (file7b.value) {
    formData.append('file_7b', file7b.value)
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
    syncSuccess.value = `${data.message} (Updated: ${data.updated}, Not Found: ${data.not_found}, Override RJM: ${data.overridden_rjm ?? 0}, Override 7B: ${data.overridden_7b ?? 0})`
    syncWarnings.value = data.warnings || []
    await loadTimestamps()
  } catch (err: any) {
    syncError.value = err.message || 'Failed to sync stock'
  } finally {
    isSyncing.value = false
  }
}

onMounted(async () => {
  loadTimestamps()
  await store.fetchConfirmedPOs()
  // Resume an in-progress fulfillment after reload / navigation
  await store.rehydrate()
})

watch(() => store.currentItem, (newItem) => {
  if (newItem) {
    // Pre-fill with previously entered qty when re-processing a done item, else the requested qty
    manualQty.value = store.doneIds.includes(newItem.id) || newItem.qty_fulfilled > 0
      ? newItem.qty_fulfilled
      : newItem.qty_request
  }
}, { immediate: true })

const recapGroups = computed(() => {
  const items = store.recapPO?.items || []
  return {
    fulfilled: items.filter(i => i.qty_fulfilled > 0 && i.qty_fulfilled >= i.qty_request),
    partial: items.filter(i => i.qty_fulfilled > 0 && i.qty_fulfilled < i.qty_request),
    empty: items.filter(i => i.qty_fulfilled === 0),
  }
})

const handleSelectPO = (po: PO) => {
  if (po.status === 'COMPLETED_BY_GUDANG') {
    // Completed POs open a read-only recap instead of the scanner
    store.openRecap(po.id)
    return
  }
  isSubmitted.value = false
  submitError.value = ''
  store.selectPO(po.id)
}

const handleJump = (itemId: string) => {
  store.jumpTo(itemId)
  showRecap.value = false
}

const handleSaveAndNext = () => {
  store.saveAndNext(Number(manualQty.value))
}

const handleSubmit = async () => {
  submitError.value = ''
  try {
    await store.submitFulfillment()
    isSubmitted.value = true
  } catch (err: any) {
    submitError.value = err?.message || 'Gagal submit fulfillment'
  }
}

const handleBack = () => {
  isSubmitted.value = false
  store.reset()
  store.fetchConfirmedPOs()
}

const fileTag = (po: PO) => `${(po.tujuan_po || 'CV GPD').replace(/\s+/g, '_')}_${po.nomor_po}`

const downloadPenjualan = (po: PO) =>
  downloadFile(`${API}/api/po/${po.id}/export/penjualan`, `Penjualan_Gudang_${fileTag(po)}.csv`)

const downloadPembelian = (po: PO) =>
  downloadFile(`${API}/api/po/${po.id}/export/pembelian`, `Pembelian_Toko_${fileTag(po)}.csv`)
</script>

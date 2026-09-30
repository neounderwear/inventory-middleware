<script setup lang="ts">
import { ref, onMounted } from 'vue'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const fileToko = ref<File | null>(null)
const entitasToko = ref<string>('JAGOAN')

// Filter controls
const hideZeroStock = ref(false)
const availableBrands = ref<string[]>([])
const selectedBrands = ref<string[]>([])

const isGenerating = ref(false)
const isGeneratingStock = ref(false)
const generateError = ref('')

const poData = ref<any>(null)
const poItems = ref<any[]>([])

const isConfirming = ref(false)
const confirmError = ref('')
const confirmSuccess = ref(false)

// Manual add item refs
const manualSku = ref('')
const manualQty = ref<number | null>(null)

// Fetch available brands on mount
const draftPOs = ref<any[]>([])

const fetchBrands = async () => {
  try {
    const res = await fetch(`${API}/api/master/brands`)
    if (res.ok) {
      availableBrands.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch brands:', err)
  }
}

const fetchDraftPOs = async () => {
  try {
    const res = await fetch(`${API}/api/po/`)
    if (res.ok) {
      const data = await res.json()
      // Show DRAFT and optionally CONFIRMED POs so they can resume viewing them
      draftPOs.value = data.filter((po: any) => po.status === 'DRAFT' || po.status === 'CONFIRMED_BY_STORE')
    }
  } catch (err) {
    console.error('Failed to fetch draft POs:', err)
  }
}

onMounted(() => {
  fetchBrands()
  fetchDraftPOs()
})

const resumePo = (id: string) => {
  fetchPoDetails(id)
}

const toggleAllBrands = () => {
  if (selectedBrands.value.length === availableBrands.value.length && availableBrands.value.length > 0) {
    selectedBrands.value = []
  } else {
    selectedBrands.value = [...availableBrands.value]
  }
}

const handleFileToko = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    fileToko.value = target.files[0]
  }
}

const generateDraft = async () => {
  if (!fileToko.value) {
    generateError.value = 'Please select the store stock file.'
    return
  }

  isGenerating.value = true
  generateError.value = ''

  const formData = new FormData()
  formData.append('file_toko', fileToko.value)
  formData.append('entitas_toko', entitasToko.value)
  if (selectedBrands.value.length > 0) {
    formData.append('selected_brands', selectedBrands.value.join(','))
  }

  try {
    const res = await fetch(`${API}/api/po/generate-draft`, {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      throw new Error(errData?.detail || `Failed to generate draft: ${res.statusText}`)
    }

    const data = await res.json()
    const poId = data.po_id || data.id
    await fetchPoDetails(poId)
  } catch (err: any) {
    generateError.value = err.message || 'An error occurred'
  } finally {
    isGenerating.value = false
  }
}

const generateUpdateStock = async () => {
  if (!fileToko.value) {
    generateError.value = 'Please select the store stock file.'
    return
  }

  isGeneratingStock.value = true
  generateError.value = ''

  const formData = new FormData()
  formData.append('file_gudang', fileToko.value)
  formData.append('entitas', entitasToko.value)
  formData.append('hide_zero_stock', String(hideZeroStock.value))
  if (selectedBrands.value.length > 0) {
    formData.append('selected_brands', selectedBrands.value.join(','))
  }

  try {
    const res = await fetch(`${API}/api/export/update-stock`, {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => null)
      throw new Error(errData?.detail || `Failed to generate update stock: ${res.statusText}`)
    }

    // Download the file
    const blob = await res.blob()
    const contentDisposition = res.headers.get('Content-Disposition') || ''
    const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/i)
    const filename = filenameMatch ? filenameMatch[1] : 'update_stock.xlsx'

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    generateError.value = err.message || 'An error occurred'
  } finally {
    isGeneratingStock.value = false
  }
}

const fetchPoDetails = async (poId: string) => {
  try {
    const res = await fetch(`${API}/api/po/${poId}`)
    if (!res.ok) throw new Error('Failed to fetch PO details')
    const data = await res.json()
    poData.value = data
    poItems.value = data.items || []
  } catch (err: any) {
    generateError.value = 'Could not load PO details after generation.'
  }
}

const removeItem = (index: number) => {
  poItems.value.splice(index, 1)
}

const addManualItem = () => {
  const sku = manualSku.value.trim()
  const qty = manualQty.value

  if (!sku) return
  if (qty == null || qty <= 0) return

  // Check if SKU already exists in the list
  const existing = poItems.value.find(item => item.sku === sku)
  if (existing) {
    existing.qty_request += qty
  } else {
    poItems.value.push({
      sku: sku,
      nama_produk: '(Manual Entry)',
      stok_sisa_toko: 0,
      stok_sisa_gudang: 0,
      qty_sistem: 0,
      qty_request: qty,
      _manual: true,
    })
  }

  // Reset inputs
  manualSku.value = ''
  manualQty.value = null
}

const confirmPo = async () => {
  if (!poData.value) return

  isConfirming.value = true
  confirmError.value = ''
  confirmSuccess.value = false

  const itemsPayload = poItems.value.map(item => ({
    sku: item.sku,
    qty_request: Number(item.qty_request)
  }))

  try {
    const res = await fetch(`${API}/api/po/${poData.value.id || poData.value.po_id}/items`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ items: itemsPayload })
    })

    if (!res.ok) {
      throw new Error(`Failed to confirm PO: ${res.statusText}`)
    }

    confirmSuccess.value = true
    poData.value.status = 'CONFIRMED_BY_STORE'
  } catch (err: any) {
    confirmError.value = err.message || 'An error occurred'
  } finally {
    isConfirming.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto p-4 space-y-8">
    <h1 class="text-4xl font-black mb-8 uppercase tracking-tight">Store Dashboard</h1>

    <!-- Section 1: Upload & Actions Form -->
    <section class="card-brutal">
      <h2 class="text-2xl font-black mb-6 uppercase">Upload & Actions</h2>

      <div class="space-y-4">
        <div class="flex flex-col">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">File Stok Toko (.xlsx)</label>
          <input type="file" accept=".xlsx" @change="handleFileToko" class="border-black border-[3px] p-2 bg-white" />
        </div>

        <div class="flex flex-col">
          <label class="font-bold mb-1 uppercase tracking-wider text-sm">Entitas Toko</label>
          <select v-model="entitasToko"
            class="w-full border-[3px] border-black p-3 bg-white font-bold uppercase cursor-pointer appearance-none shadow-[4px_4px_0_0_rgba(0,0,0,1)] focus:outline-none">
            <option value="JAGOAN">JAGOAN</option>
            <option value="RJM">RJM</option>
            <option value="7B">7B</option>
          </select>
        </div>

        <!-- Filters Section -->
        <div class="border-black border-[3px] p-4 bg-gray-50 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
          <h3 class="font-black text-sm uppercase tracking-wider mb-3">Filters</h3>
          <div class="flex flex-col gap-5">
            <!-- Brand Whitelist Checkboxes -->
            <div class="flex flex-col">
              <div class="flex justify-between items-center mb-2 mt-2">
                <span class="text-xs font-bold uppercase">Pilih Brand Yang Ingin Di-PO (Kosongkan = Semua)</span>
                <button @click.prevent="toggleAllBrands" class="text-xs font-bold uppercase border-2 border-black px-2 py-1 bg-yellow-200 hover:bg-yellow-300 cursor-pointer shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-y-[1px] active:translate-x-[1px] active:shadow-none transition-all">
                  {{ selectedBrands.length === availableBrands.length && availableBrands.length > 0 ? 'Uncentang Semua' : 'Centang Semua' }}
                </button>
              </div>
              <div v-if="availableBrands.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-y-4 gap-x-2 mt-3 p-4 border-[3px] border-black bg-white shadow-[4px_4px_0_0_rgba(0,0,0,1)]">
                <label v-for="brand in availableBrands" :key="brand" class="flex items-center space-x-3 cursor-pointer select-none">
                  <input type="checkbox" :value="brand" v-model="selectedBrands" class="w-5 h-5 border-2 border-black rounded-none cursor-pointer accent-black" />
                  <span class="uppercase font-bold text-sm tracking-wide">{{ brand }}</span>
                </label>
              </div>
              <div v-else class="text-sm font-bold text-gray-400 italic">Loading brands...</div>
            </div>

            <!-- Hide Zero Stock Checkbox (Only for Update Stock) -->
            <div class="p-3 border-[2px] border-black bg-yellow-100 flex items-center justify-between">
              <label class="flex items-center gap-3 cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  v-model="hideZeroStock" 
                  class="w-6 h-6 border-[2px] border-black accent-black cursor-pointer"
                />
                <span class="font-bold text-sm uppercase tracking-wider">Hide Zero Stock</span>
              </label>
              <span class="text-xs font-bold text-gray-600 uppercase">(Only applies to Update Stock)</span>
            </div>
          </div>
        </div>

        <div v-if="generateError" class="bg-pink-300 border-black border-[3px] p-3 font-bold">
          {{ generateError }}
        </div>

        <div class="flex gap-4 mt-4">
          <button v-if="entitasToko !== '7B'" @click="generateDraft" :disabled="isGenerating" class="btn-brutal bg-yellow-300 flex-1">
            {{ isGenerating ? 'GENERATING...' : 'GENERATE DRAFT PO' }}
          </button>
          <button @click="generateUpdateStock" :disabled="isGeneratingStock" class="btn-brutal bg-lime-300 flex-1">
            {{ isGeneratingStock ? 'GENERATING...' : 'GENERATE UPDATE STOCK' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Session Resume Section -->
    <section v-if="!poData && draftPOs.length > 0" class="card-brutal bg-gray-50">
      <h2 class="text-2xl font-black mb-4 uppercase">Resume Active POs</h2>
      <p class="font-bold mb-4 text-sm">POs automatically clear after 24 hours.</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="po in draftPOs" :key="po.id" class="border-[3px] border-black p-4 bg-yellow-100 flex justify-between items-center cursor-pointer shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:translate-y-[2px] hover:translate-x-[2px] hover:shadow-none transition-all" @click="resumePo(po.id)">
          <div>
            <div class="font-black text-xl">{{ po.nomor_po }}</div>
            <div class="text-sm font-bold">{{ po.entitas_toko }} - <span :class="po.status === 'DRAFT' ? 'text-red-600' : 'text-green-600'">{{ po.status }}</span></div>
            <div class="text-xs font-bold mt-1 bg-black text-white px-1 inline-block">{{ po.item_count }} Items</div>
          </div>
          <div class="text-2xl font-black">▶</div>
        </div>
      </div>
    </section>

    <!-- Section 2: Draft PO Detail -->
    <section v-if="poData" class="card-brutal">
      <h2 class="text-2xl font-black mb-4 uppercase">Draft PO Details</h2>

      <div class="flex flex-wrap gap-6 mb-6">
        <div class="border-black border-[3px] p-3 bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
          <span class="block text-sm font-bold uppercase tracking-wider">Nomor PO</span>
          <span class="text-lg">{{ poData.nomor_po || poData.id }}</span>
        </div>
        <div class="border-black border-[3px] p-3 bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
          <span class="block text-sm font-bold uppercase tracking-wider">Entitas Toko</span>
          <span class="text-lg">{{ poData.entitas_toko }}</span>
        </div>
        <div class="border-black border-[3px] p-3 bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
          <span class="block text-sm font-bold uppercase tracking-wider">Status</span>
          <span class="text-lg font-bold"
            :class="{ 'text-pink-600': poData.status !== 'CONFIRMED_BY_STORE', 'text-cyan-600': poData.status === 'CONFIRMED_BY_STORE' }">
            {{ poData.status }}
          </span>
        </div>
      </div>

      <div class="overflow-x-auto border-black border-[3px]">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-200">
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">SKU</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">Nama Produk</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">Stok Toko</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">Stok Gudang</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">Qty Sistem</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider">Qty Request</th>
              <th class="border-black border-[3px] p-3 uppercase text-sm tracking-wider w-16 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in poItems" :key="item.sku + '-' + index"
              :class="index % 2 === 0 ? 'bg-white' : 'bg-gray-50'">
              <td class="border-black border-[3px] p-3 font-mono">{{ item.sku }}</td>
              <td class="border-black border-[3px] p-3">{{ item.nama_produk }}</td>
              <td class="border-black border-[3px] p-3">{{ item.stok_sisa_toko }}</td>
              <td class="border-black border-[3px] p-3">{{ item.stok_sisa_gudang }}</td>
              <td class="border-black border-[3px] p-3">{{ item.qty_sistem }}</td>
              <td class="border-black border-[3px] p-2">
                <input type="number" v-model.number="item.qty_request"
                  class="border-black border-[2px] p-1 w-24 focus:outline-none focus:ring-2 focus:ring-cyan-300"
                  min="0" />
              </td>
              <td class="border-black border-[3px] p-2 text-center">
                <button @click="removeItem(index)"
                  class="px-3 py-1 font-bold border-[2px] border-black bg-red-400 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all duration-100 cursor-pointer select-none active:translate-y-[1px] active:translate-x-[1px] active:shadow-none hover:bg-red-500 text-white text-sm">
                  X
                </button>
              </td>
            </tr>
            <tr v-if="poItems.length === 0">
              <td colspan="7" class="border-black border-[3px] p-4 text-center font-bold">
                No items found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Manual Add Item Form -->
      <div class="mt-4 flex flex-wrap items-end gap-3">
        <div class="flex flex-col">
          <label class="font-bold mb-1 uppercase tracking-wider text-xs">SKU</label>
          <input type="text" v-model="manualSku" placeholder="Search SKU..."
            class="border-black border-[2px] p-2 w-48 focus:outline-none focus:ring-2 focus:ring-cyan-300" />
        </div>
        <div class="flex flex-col">
          <label class="font-bold mb-1 uppercase tracking-wider text-xs">Qty</label>
          <input type="number" v-model.number="manualQty" placeholder="Qty" min="1"
            class="border-black border-[2px] p-2 w-24 focus:outline-none focus:ring-2 focus:ring-cyan-300" />
        </div>
        <button @click="addManualItem" class="btn-brutal bg-violet-300 text-sm">
          ADD ITEM
        </button>
      </div>

      <!-- Section 3: Confirm Button -->
      <div class="mt-8">
        <div v-if="confirmError" class="bg-pink-300 border-black border-[3px] p-3 font-bold mb-4">
          {{ confirmError }}
        </div>
        <div v-if="confirmSuccess" class="bg-green-300 border-black border-[3px] p-3 font-bold mb-4">
          PO Confirmed Successfully!
        </div>

        <button @click="confirmPo" :disabled="isConfirming || poData.status === 'CONFIRMED_BY_STORE'"
          class="btn-brutal bg-cyan-300 text-xl w-full py-4"
          :class="{ 'opacity-50 cursor-not-allowed': poData.status === 'CONFIRMED_BY_STORE' }">
          {{ isConfirming ? 'CONFIRMING...' : 'CONFIRM PO' }}
        </button>
      </div>
    </section>
  </div>
</template>

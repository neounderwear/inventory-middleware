<template>
  <div class="max-w-4xl mx-auto p-4 space-y-8">
    <h1 class="text-4xl font-black uppercase tracking-tight border-black border-[3px] bg-white p-4 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] inline-block">
      📊 UPDATE STOCK RESELLER
    </h1>

    <div v-if="error" class="card-brutal bg-red-300 text-black font-bold">
      {{ error }}
    </div>
    
    <div v-if="success" class="card-brutal bg-green-300 text-black font-bold">
      {{ success }}
    </div>

    <!-- Section 1: Upload -->
    <div class="card-brutal space-y-4">
      <h2 class="text-2xl font-bold">1. Upload File Sisa Stok Olsera</h2>
      <p class="font-medium">Please upload the current stock file export from Olsera (.xlsx)</p>
      
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-bold uppercase tracking-wider text-sm">Pilih Entitas</label>
          <select v-model="entitas" class="w-full border-[3px] border-black p-3 bg-white font-bold uppercase cursor-pointer appearance-none shadow-[4px_4px_0_0_rgba(0,0,0,1)] focus:outline-none">
            <option value="GUDANG">Gudang</option>
            <option value="JAGOAN">Jagoan</option>
            <option value="RJM">RJM</option>
            <option value="7B">7B</option>
          </select>
        </div>

        <div class="flex flex-col gap-2">
          <label class="font-bold uppercase tracking-wider text-sm">File Stok (.xlsx)</label>
          <input 
            type="file" 
            accept=".xlsx"
            @change="handleFileUpload"
            class="border-black border-[3px] p-2 bg-white w-full cursor-pointer shadow-[4px_4px_0_0_rgba(0,0,0,1)] focus:outline-none"
          />
          <div v-if="file" class="text-green-700 font-bold mt-2">
            Selected: {{ file.name }}
          </div>
        </div>
      </div>
    </div>

    <!-- Section 2: Filter Controls -->
    <div class="card-brutal bg-yellow-100 space-y-4">
      <h2 class="text-2xl font-bold">2. Filters & Configuration</h2>
      
      <div class="space-y-4">
        <label class="flex items-center gap-3 cursor-pointer select-none w-max">
          <input 
            type="checkbox" 
            v-model="hideZeroStock"
            class="w-6 h-6 border-black border-[3px] accent-black cursor-pointer shadow-[3px_3px_0_0_rgba(0,0,0,1)]"
          />
          <span class="font-bold text-lg">Hide Zero Stock</span>
        </label>

        <div class="space-y-2">
          <div class="flex justify-between items-center mb-2 mt-2">
            <span class="text-xs font-bold uppercase">Pilih Brand Yang Ingin Di-Update (Kosongkan = Semua)</span>
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
      </div>
    </div>

    <!-- Section 3: Generate Action -->
    <div class="pt-4">
      <button 
        @click="generateStockUpdate"
        :disabled="loading || !file"
        class="btn-brutal bg-pink-300 w-full py-4 text-2xl flex items-center justify-center gap-2"
        :class="{ 'opacity-50 cursor-not-allowed': loading || !file }"
      >
        <span v-if="loading">GENERATING...</span>
        <span v-else>GENERATE STOCK UPDATE</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const file = ref<File | null>(null)
const entitas = ref<string>('GUDANG')
const hideZeroStock = ref<boolean>(true)
const availableBrands = ref<string[]>([])
const selectedBrands = ref<string[]>([])
const loading = ref<boolean>(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

onMounted(() => {
  fetchBrands()
})

const toggleAllBrands = () => {
  if (selectedBrands.value.length === availableBrands.value.length && availableBrands.value.length > 0) {
    selectedBrands.value = []
  } else {
    selectedBrands.value = [...availableBrands.value]
  }
}

const handleFileUpload = (event: Event) => {
  error.value = null
  success.value = null
  
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const selectedFile = target.files[0]
    if (!selectedFile.name.endsWith('.xlsx')) {
      error.value = 'Please upload a valid .xlsx file.'
      file.value = null
      target.value = ''
      return
    }
    file.value = selectedFile
  }
}

const generateStockUpdate = async () => {
  if (!file.value) {
    error.value = 'Please upload a file first.'
    return
  }

  loading.value = true
  error.value = null
  success.value = null

  try {
    const formData = new FormData()
    formData.append('file_gudang', file.value)
    formData.append('entitas', entitas.value)
    formData.append('hide_zero_stock', hideZeroStock.value.toString())
    if (selectedBrands.value.length > 0) {
      formData.append('selected_brands', selectedBrands.value.join(','))
    }

    const response = await fetch(`${API}/api/export/update-stock`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`Server Error (${response.status}): ${errText || 'Unknown error'}`)
    }

    const blob = await response.blob()
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    // Extract filename from content-disposition header if available
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `update_stock_${entitas.value.toLowerCase()}.xlsx`
    if (contentDisposition && contentDisposition.includes('filename=')) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/)
      if (match && match[1]) {
        filename = match[1]
      }
    }
    
    a.download = filename
    document.body.appendChild(a)
    a.click()
    
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    success.value = 'Stock update generated and downloaded successfully!'
  } catch (err: any) {
    error.value = err.message || 'Failed to generate stock update.'
    console.error('Export error:', err)
  } finally {
    loading.value = false
  }
}
</script>

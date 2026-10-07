<template>
  <main class="p-8 max-w-6xl mx-auto space-y-12">
    <div class="mb-12 text-center">
      <h1 class="text-4xl md:text-5xl font-black mb-4 uppercase tracking-tighter">Inventory Middleware</h1>
      <p class="text-xl font-bold inline-block">
        <span class="bg-black text-white px-2 py-1">Sistem Manajemen Stok dan Purchase Order</span>
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
      <router-link to="/po"
        class="card-brutal bg-yellow-300 text-black no-underline hover:-translate-y-1 transition-transform min-h-50 flex flex-col justify-center text-center">
        <h2 class="uppercase font-black text-3xl mb-2">📦 PO</h2>
        <p class="font-semibold text-lg">Kelola Purchase Order Toko</p>
      </router-link>

      <router-link to="/gudang"
        class="card-brutal bg-cyan-300 text-black no-underline hover:-translate-y-1 transition-transform min-h-50 flex flex-col justify-center text-center">
        <h2 class="uppercase font-black text-3xl mb-2">🏭 Fulfillment</h2>
        <p class="font-semibold text-lg">Proses & Ambil Barang</p>
      </router-link>

      <router-link to="/update-stock"
        class="card-brutal bg-pink-300 text-black no-underline hover:-translate-y-1 transition-transform min-h-50 flex flex-col justify-center text-center">
        <h2 class="uppercase font-black text-3xl mb-2">📊 Update</h2>
        <p class="font-semibold text-lg">Generate Laporan Stok</p>
      </router-link>

      <router-link to="/upload"
        class="card-brutal bg-violet-300 text-black no-underline hover:-translate-y-1 transition-transform min-h-50 flex flex-col justify-center text-center">
        <h2 class="uppercase font-black text-3xl mb-2">📥 Upload</h2>
        <p class="font-semibold text-lg">Upload Data</p>
      </router-link>
    </div>
  </main>
</template>

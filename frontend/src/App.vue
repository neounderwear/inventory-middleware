<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isMobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const navLinks = [
  { path: '/', label: 'Home' },
  { path: '/po', label: 'PO' },
  { path: '/fullfillment', label: 'Fullfillment' },
  { path: '/update-stock', label: 'Update Stock' },
  { path: '/upload', label: 'Upload' }
]
</script>

<template>
  <div class="min-h-screen bg-[#f8fafc] text-black">
    <nav class="sticky top-0 z-50 bg-white border-b-brutal border-black">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <router-link to="/" class="shrink-0 flex items-center no-underline text-black">
              <span class="font-black text-2xl md:text-3xl tracking-tighter uppercase">Inventory Middleware</span>
            </router-link>
          </div>

          <!-- Desktop menu -->
          <div class="hidden sm:flex sm:items-center sm:space-x-3">
            <router-link v-for="link in navLinks" :key="link.path" :to="link.path"
              class="btn-brutal py-1.5! px-4! text-sm! no-underline text-black"
              :class="[route.path === link.path ? 'bg-yellow-300' : 'bg-white']">
              {{ link.label }}
            </router-link>
          </div>

          <!-- Mobile menu button -->
          <div class="flex items-center sm:hidden">
            <button @click="toggleMobileMenu" class="btn-brutal p-2!" aria-label="Toggle menu">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path v-if="!isMobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="3"
                  d="M4 6h16M4 12h16M4 18h16" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-show="isMobileMenuOpen" class="sm:hidden border-t-brutal border-black bg-white">
        <div class="pt-2 pb-3 space-y-2 px-4">
          <router-link v-for="link in navLinks" :key="link.path" :to="link.path" @click="isMobileMenuOpen = false"
            class="btn-brutal block w-full text-center no-underline text-black"
            :class="[route.path === link.path ? 'bg-yellow-300' : 'bg-white']">
            {{ link.label }}
          </router-link>
        </div>
      </div>
    </nav>

    <div class="py-8">
      <router-view />
    </div>
  </div>
</template>

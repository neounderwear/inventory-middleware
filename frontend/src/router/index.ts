import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/toko',
      name: 'toko',
      component: () => import('../views/TokoView.vue')
    },
    {
      path: '/gudang',
      name: 'gudang',
      component: () => import('../views/GudangView.vue')
    },
    {
      path: '/update-stock',
      name: 'update-stock',
      component: () => import('../views/UpdateStockView.vue')
    }
  ]
})

export default router

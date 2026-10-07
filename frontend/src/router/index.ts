import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/po",
      name: "po",
      component: () => import("../views/TokoView.vue"),
    },
    {
      path: "/fullfillment",
      name: "fullfillment",
      component: () => import("../views/GudangView.vue"),
    },
    {
      path: "/update-stock",
      name: "update-stock",
      component: () => import("../views/UpdateStockView.vue"),
    },
    {
      path: "/upload",
      name: "upload",
      component: () => import("../views/UploadView.vue"),
    },
  ],
});

export default router;

import { defineStore } from "pinia";
import { ref, computed } from "vue";

const API = "";

export interface POItem {
  id: string;
  sku: string;
  nama_produk: string;
  stok_sisa_toko: number;
  stok_sisa_gudang: number;
  qty_sistem: number;
  qty_request: number;
  qty_fulfilled: number;
}

export interface PO {
  id: string;
  nomor_po: string;
  entitas_toko: string;
  tanggal_dibuat: string;
  status: string;
  items: POItem[];
}

export const useFulfillmentStore = defineStore("fulfillment", () => {
  const availablePOs = ref<PO[]>([]);
  const currentPO = ref<PO | null>(null);
  const currentIndex = ref(0);
  const isCompleted = ref(false);
  const isLoading = ref(false);

  const fetchConfirmedPOs = async () => {
    isLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/`);
      const data = await res.json();
      availablePOs.value = data.filter((po: PO) => po.status === "CONFIRMED_BY_STORE" || po.status === "COMPLETED_BY_GUDANG");
    } catch (error) {
      console.error(error);
    } finally {
      isLoading.value = false;
    }
  };

  const selectPO = async (poId: string) => {
    isLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/${poId}/`);
      const data = await res.json();
      currentPO.value = data;
      currentIndex.value = 0;
      isCompleted.value = false;
    } catch (error) {
      console.error(error);
    } finally {
      isLoading.value = false;
    }
  };

  const advanceToNext = () => {
    if (currentPO.value && currentIndex.value < currentPO.value.items.length - 1) {
      currentIndex.value++;
    } else {
      isCompleted.value = true;
    }
  };

  const markReady = () => {
    if (!currentPO.value) return;
    const item = currentPO.value.items[currentIndex.value];
    item.qty_fulfilled = item.qty_request;
    advanceToNext();
  };

  const markPartial = (qty: number) => {
    if (!currentPO.value) return;
    const item = currentPO.value.items[currentIndex.value];
    item.qty_fulfilled = qty;
    advanceToNext();
  };

  const markEmpty = () => {
    if (!currentPO.value) return;
    const item = currentPO.value.items[currentIndex.value];
    item.qty_fulfilled = 0;
    advanceToNext();
  };

  const saveAndNext = (qty: number) => {
    if (!currentPO.value) return;
    const item = currentPO.value.items[currentIndex.value];
    item.qty_fulfilled = qty;
    advanceToNext();
  };

  const submitFulfillment = async () => {
    if (!currentPO.value) return;
    isLoading.value = true;
    try {
      await fetch(`${API}/api/po/${currentPO.value.id}/fulfill`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          items: currentPO.value.items.map((item) => ({
            sku: item.sku,
            qty_fulfilled: item.qty_fulfilled,
          })),
        }),
      });
    } catch (error) {
      console.error(error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const reset = () => {
    currentPO.value = null;
    currentIndex.value = 0;
    isCompleted.value = false;
  };

  const currentItem = computed(() => {
    if (!currentPO.value) return null;
    return currentPO.value.items[currentIndex.value] || null;
  });

  const totalItems = computed(() => currentPO.value?.items.length || 0);

  const progress = computed(() => {
    if (totalItems.value === 0) return "0 / 0";
    return `${Math.min(currentIndex.value + 1, totalItems.value)} / ${totalItems.value}`;
  });

  const fulfilledItems = computed(() => {
    if (!currentPO.value) return [];
    return currentPO.value.items.filter((item) => item.qty_fulfilled === item.qty_request);
  });

  const partialItems = computed(() => {
    if (!currentPO.value) return [];
    return currentPO.value.items.filter((item) => item.qty_fulfilled !== undefined && item.qty_fulfilled > 0 && item.qty_fulfilled < item.qty_request);
  });

  const emptyItems = computed(() => {
    if (!currentPO.value) return [];
    return currentPO.value.items.filter((item) => item.qty_fulfilled === 0);
  });

  return {
    availablePOs,
    currentPO,
    currentIndex,
    isCompleted,
    isLoading,
    fetchConfirmedPOs,
    selectPO,
    markReady,
    markPartial,
    markEmpty,
    saveAndNext,
    advanceToNext,
    submitFulfillment,
    reset,
    currentItem,
    progress,
    totalItems,
    fulfilledItems,
    partialItems,
    emptyItems,
  };
});

import { defineStore } from "pinia";
import { ref, computed } from "vue";

const API = "";

export interface POItem {
  id: string;
  sku: string;
  nama_produk: string;
  brand?: string | null;
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
  tujuan_po?: string | null;
  tanggal_dibuat: string;
  status: string;
  item_count?: number;
  items: POItem[];
}

/** Shape persisted to localStorage for one in-progress PO. */
interface SavedProgress {
  poId: string;
  qty: Record<string, number>; // itemId -> qty_fulfilled
  queue: string[]; // pending item ids, in processing order (front = current)
  doneIds: string[]; // processed item ids
  skippedIds: string[]; // item ids that were skipped at least once and are still pending
  savedAt: string;
}

const ACTIVE_KEY = "fulfillment:active";
const progressKey = (poId: string) => `fulfillment:po:${poId}`;

const loadProgress = (poId: string): SavedProgress | null => {
  try {
    const raw = localStorage.getItem(progressKey(poId));
    return raw ? (JSON.parse(raw) as SavedProgress) : null;
  } catch {
    return null;
  }
};

const clearProgress = (poId: string) => {
  localStorage.removeItem(progressKey(poId));
  if (localStorage.getItem(ACTIVE_KEY) === poId) localStorage.removeItem(ACTIVE_KEY);
};

export const useFulfillmentStore = defineStore("fulfillment", () => {
  const availablePOs = ref<PO[]>([]);
  const currentPO = ref<PO | null>(null);
  const queue = ref<string[]>([]);
  const doneIds = ref<string[]>([]);
  const skippedIds = ref<string[]>([]);
  const isLoading = ref(false);
  const savedProgressIds = ref<string[]>([]);

  // Read-only recap for COMPLETED_BY_GUDANG POs
  const recapPO = ref<PO | null>(null);
  const isRecapLoading = ref(false);

  // ---------- Persistence ----------

  const persist = () => {
    if (!currentPO.value) return;
    const qty: Record<string, number> = {};
    for (const item of currentPO.value.items) qty[item.id] = item.qty_fulfilled;
    const state: SavedProgress = {
      poId: currentPO.value.id,
      qty,
      queue: queue.value,
      doneIds: doneIds.value,
      skippedIds: skippedIds.value,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(progressKey(currentPO.value.id), JSON.stringify(state));
    localStorage.setItem(ACTIVE_KEY, currentPO.value.id);
    if (!savedProgressIds.value.includes(currentPO.value.id)) {
      savedProgressIds.value = [...savedProgressIds.value, currentPO.value.id];
    }
  };

  const refreshSavedProgressIds = () => {
    savedProgressIds.value = availablePOs.value
      .filter((po) => po.status === "CONFIRMED_BY_STORE" && loadProgress(po.id))
      .map((po) => po.id);
  };

  // ---------- Loading ----------

  const fetchConfirmedPOs = async () => {
    isLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/`);
      const data = await res.json();
      availablePOs.value = data.filter(
        (po: PO) => po.status === "CONFIRMED_BY_STORE" || po.status === "COMPLETED_BY_GUDANG"
      );
      // Drop stale progress for POs that are no longer pending fulfillment
      for (const po of availablePOs.value) {
        if (po.status === "COMPLETED_BY_GUDANG") clearProgress(po.id);
      }
      refreshSavedProgressIds();
    } catch (error) {
      console.error(error);
    } finally {
      isLoading.value = false;
    }
  };

  /** Start or resume fulfillment of a CONFIRMED_BY_STORE PO. */
  const selectPO = async (poId: string) => {
    isLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/${poId}`);
      if (!res.ok) throw new Error("Failed to fetch PO");
      const data: PO = await res.json();

      if (data.status !== "CONFIRMED_BY_STORE") {
        // Nothing to scan — drop any stale local state
        clearProgress(poId);
        return;
      }

      const allIds = data.items.map((i) => i.id);
      const saved = loadProgress(poId);

      if (saved) {
        // Rehydrate: restore quantities, queue, done & skipped lists
        for (const item of data.items) {
          if (saved.qty[item.id] !== undefined) item.qty_fulfilled = saved.qty[item.id];
        }
        const valid = new Set(allIds);
        const done = saved.doneIds.filter((id) => valid.has(id));
        const q = saved.queue.filter((id) => valid.has(id) && !done.includes(id));
        // Any item not present in saved state (e.g. added later) goes to the end of the queue
        for (const id of allIds) if (!done.includes(id) && !q.includes(id)) q.push(id);
        doneIds.value = done;
        queue.value = q;
        skippedIds.value = (saved.skippedIds || []).filter((id) => q.includes(id));
      } else {
        doneIds.value = [];
        queue.value = allIds;
        skippedIds.value = [];
      }

      currentPO.value = data;
      persist();
    } catch (error) {
      console.error(error);
    } finally {
      isLoading.value = false;
    }
  };

  /** Resume the last active PO after a reload / navigation. */
  const rehydrate = async () => {
    if (currentPO.value) return;
    const activeId = localStorage.getItem(ACTIVE_KEY);
    if (activeId) await selectPO(activeId);
  };

  // ---------- Scanning actions ----------

  const itemById = (id: string) => currentPO.value?.items.find((i) => i.id === id) || null;

  const currentItem = computed(() => (queue.value.length ? itemById(queue.value[0]) : null));

  const completeCurrent = (qty: number) => {
    const item = currentItem.value;
    if (!item) return;
    item.qty_fulfilled = Math.max(0, Math.floor(Number(qty) || 0));
    queue.value = queue.value.slice(1);
    if (!doneIds.value.includes(item.id)) doneIds.value = [...doneIds.value, item.id];
    skippedIds.value = skippedIds.value.filter((id) => id !== item.id);
    persist();
  };

  const saveAndNext = (qty: number) => completeCurrent(qty);
  const markReady = () => currentItem.value && completeCurrent(currentItem.value.qty_request);
  const markPartial = (qty: number) => completeCurrent(qty);
  const markEmpty = () => completeCurrent(0);

  /** "LEWATI SEMENTARA": move the current item to the back of the queue. */
  const skipCurrent = () => {
    if (queue.value.length < 2) return;
    const [first, ...rest] = queue.value;
    queue.value = [...rest, first];
    if (!skippedIds.value.includes(first)) skippedIds.value = [...skippedIds.value, first];
    persist();
  };

  /** Bring any item (pending or done) to the front of the queue to (re)process it. */
  const jumpTo = (itemId: string) => {
    if (!itemById(itemId)) return;
    doneIds.value = doneIds.value.filter((id) => id !== itemId);
    queue.value = [itemId, ...queue.value.filter((id) => id !== itemId)];
    persist();
  };

  const submitFulfillment = async () => {
    if (!currentPO.value) return;
    isLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/${currentPO.value.id}/fulfill`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: currentPO.value.items.map((item) => ({
            sku: item.sku,
            qty_fulfilled: item.qty_fulfilled,
          })),
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Submit failed");
      }
      // Only now is the local progress for this PO discarded
      clearProgress(currentPO.value.id);
      savedProgressIds.value = savedProgressIds.value.filter((id) => id !== currentPO.value!.id);
      currentPO.value.status = "COMPLETED_BY_GUDANG";
    } catch (error) {
      console.error(error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  /** Leave the scanner. Progress for the PO stays saved so it can be resumed later. */
  const reset = () => {
    localStorage.removeItem(ACTIVE_KEY);
    currentPO.value = null;
    queue.value = [];
    doneIds.value = [];
    skippedIds.value = [];
  };

  // ---------- Read-only recap ----------

  const openRecap = async (poId: string) => {
    isRecapLoading.value = true;
    try {
      const res = await fetch(`${API}/api/po/${poId}`);
      if (!res.ok) throw new Error("Failed to fetch PO");
      recapPO.value = await res.json();
    } catch (error) {
      console.error(error);
      alert("Gagal memuat rekap PO");
    } finally {
      isRecapLoading.value = false;
    }
  };

  const closeRecap = () => {
    recapPO.value = null;
  };

  // ---------- Derived state ----------

  const isCompleted = computed(() => !!currentPO.value && queue.value.length === 0);
  const totalItems = computed(() => currentPO.value?.items.length || 0);
  const doneCount = computed(() => doneIds.value.length);
  const progress = computed(() => `${doneCount.value} / ${totalItems.value}`);
  const progressPercent = computed(() =>
    totalItems.value ? (doneCount.value / totalItems.value) * 100 : 0
  );

  const doneItems = computed(() =>
    doneIds.value.map(itemById).filter((i): i is POItem => !!i)
  );
  const pendingItems = computed(() =>
    queue.value.map(itemById).filter((i): i is POItem => !!i)
  );

  const fulfilledItems = computed(() =>
    doneItems.value.filter((i) => i.qty_fulfilled >= i.qty_request && i.qty_fulfilled > 0)
  );
  const partialItems = computed(() =>
    doneItems.value.filter((i) => i.qty_fulfilled > 0 && i.qty_fulfilled < i.qty_request)
  );
  const emptyItems = computed(() => doneItems.value.filter((i) => i.qty_fulfilled === 0));

  return {
    availablePOs,
    currentPO,
    queue,
    doneIds,
    skippedIds,
    isLoading,
    savedProgressIds,
    recapPO,
    isRecapLoading,
    fetchConfirmedPOs,
    selectPO,
    rehydrate,
    markReady,
    markPartial,
    markEmpty,
    saveAndNext,
    skipCurrent,
    jumpTo,
    submitFulfillment,
    reset,
    openRecap,
    closeRecap,
    currentItem,
    isCompleted,
    progress,
    progressPercent,
    totalItems,
    doneCount,
    doneItems,
    pendingItems,
    fulfilledItems,
    partialItems,
    emptyItems,
  };
});

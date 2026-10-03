const API = "";

export type SyncTimestamps = {
  last_master_sync: string | null;
  last_gpd_sync: string | null;
  last_rjm_sync: string | null;
  last_7b_sync: string | null;
};

/** Format an ISO timestamp as e.g. "03 Oct 2026, 14:30 WIB" (Asia/Jakarta). */
export const formatWIB = (iso: string | null | undefined): string => {
  if (!iso) return "Belum pernah";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "Belum pernah";
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Jakarta",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(d);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("day")} ${get("month")} ${get("year")}, ${get("hour")}:${get("minute")} WIB`;
};

export const fetchTimestamps = async (): Promise<SyncTimestamps | null> => {
  try {
    const res = await fetch(`${API}/api/metadata/timestamps`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch timestamps:", err);
    return null;
  }
};

/**
 * Download a file via fetch + Blob. Uses the server-provided filename
 * (Content-Disposition) when available, otherwise falls back to `fallbackName`.
 */
export const downloadFile = async (url: string, fallbackName: string) => {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Download failed");
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match?.[1] || fallbackName;
    const blob = await res.blob();
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);
  } catch (err) {
    console.error(err);
    alert("Failed to download file");
  }
};

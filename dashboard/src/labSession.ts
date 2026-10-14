import { API_URL } from "./api";
import type { LabBoundary } from "./types";

const STORAGE_KEY = `cybersim.lab-session.v1:${API_URL}`;

export function readLabBoundary(): LabBoundary | null {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    return value && Number.isInteger(value.after_run_id) && value.after_run_id >= 0
      && Number.isInteger(value.after_campaign_id) && value.after_campaign_id >= 0 ? value : null;
  } catch {
    return null;
  }
}

export function saveLabBoundary(boundary: LabBoundary) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(boundary));
}

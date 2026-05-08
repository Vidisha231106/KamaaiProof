import axios from "axios";
import { supabase } from "./supabaseClient";

const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BACKEND_API_URL,
  timeout: 240000
});

async function getAuthHeaders() {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** POST /parse — submit documents for processing. */
export async function parseDocuments(formData) {
  const authHeaders = await getAuthHeaders();
  const response = await api.post("/parse", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      ...authHeaders
    }
  });
  return response.data;
}

/**
 * GET /session/{sessionId} — re-fetch a previously processed session.
 * Used by ResultPage when the user navigates back without router state.
 */
export async function fetchSession(sessionId) {
  const authHeaders = await getAuthHeaders();
  const response = await api.get(`/session/${sessionId}`, {
    headers: {
      ...authHeaders
    }
  });
  return response.data;
}

export { BACKEND_API_URL };

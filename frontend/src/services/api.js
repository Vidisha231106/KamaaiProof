import axios from "axios";

const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BACKEND_API_URL,
  timeout: 240000
});

/** POST /parse — submit documents for processing. */
export async function parseDocuments(formData) {
  const response = await api.post("/parse", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return response.data;
}

/**
 * GET /session/{sessionId} — re-fetch a previously processed session.
 * Used by ResultPage when the user navigates back without router state.
 */
export async function fetchSession(sessionId) {
  const response = await api.get(`/session/${sessionId}`);
  return response.data;
}

export { BACKEND_API_URL };

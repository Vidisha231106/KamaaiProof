import axios from "axios";

const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BACKEND_API_URL,
  timeout: 30000
});

export async function parseDocuments(formData) {
  const response = await api.post("/parse", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });

  return response.data;
}

export { BACKEND_API_URL };

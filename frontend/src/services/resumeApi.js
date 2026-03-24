import axios from "axios";

const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000" });

export const parseResume = (formData) =>
  api.post("/api/v1/parse", formData, { headers: { "Content-Type": "multipart/form-data" } });

export const rankResumes = (formData) =>
  api.post("/api/v1/rank", formData, { headers: { "Content-Type": "multipart/form-data" } });

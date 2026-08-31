import axios, { AxiosInstance } from "axios";
import { SystemHealth } from "../types";

export const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Standard error logging / envelope extraction
    const customError = error.response?.data?.error || {
      code: "NETWORK_ERROR",
      message: error.message || "An unexpected error occurred.",
    };
    return Promise.reject(customError);
  }
);

export const systemApi = {
  getHealth: async (): Promise<SystemHealth> => {
    const response = await apiClient.get<SystemHealth>("/health");
    return response.data;
  },
};

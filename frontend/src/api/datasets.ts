import { apiClient } from "./client";
import { DatasetVersion, DatasetSummary } from "../types/dataset";
import { ApiResponse } from "../types";

export const datasetApi = {
  getVersions: async (): Promise<DatasetVersion[]> => {
    const res = await apiClient.get<ApiResponse<any>>("/datasets");
    const payload = res.data.data;
    if (Array.isArray(payload)) {
      return payload;
    }
    if (payload && Array.isArray(payload.versions)) {
      return payload.versions;
    }
    return [];
  },
  getDetail: async (version: string) => {
    const res = await apiClient.get(`/datasets/${version}`);
    return res.data;
  },
  getSummary: async (version: string): Promise<DatasetSummary> => {
    const res = await apiClient.get<ApiResponse<DatasetSummary>>(`/datasets/${version}/summary`);
    return res.data.data; // adjust based on actual api response if needed
  },
  getManifest: async (version: string) => {
    const res = await apiClient.get(`/datasets/${version}/manifest`);
    return res.data;
  },
  getCanonicalStatus: async () => {
    const res = await apiClient.get<ApiResponse<any>>("/datasets/canonical-status");
    return res.data.data;
  },
};


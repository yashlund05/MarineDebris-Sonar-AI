import { apiClient } from "./client";
import { ApiResponse, ModelRegistryItem, ModelTask } from "../types";

export interface ListModelsParams {
  task?: ModelTask;
}

export const modelsApi = {
  getModels: async (params?: ListModelsParams): Promise<ApiResponse<ModelRegistryItem[]>> => {
    const response = await apiClient.get<ApiResponse<ModelRegistryItem[]>>("/models", { params });
    return response.data;
  },
};

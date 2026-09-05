import { apiClient } from "./client";
import { ApiResponse, ModelTask } from "../types";
import {
  ModelMetricsResponse,
  PromotionDecisionResponse,
  MultiSeedRunsResponse,
  ModelArtifactsResponse,
  ModelExplanationResponse,
  RegisteredModelSummary
} from "../types/modelEvaluation";

export interface ListModelsParams {
  task?: ModelTask;
}

export const modelsApi = {
  getModels: async (params?: ListModelsParams): Promise<ApiResponse<RegisteredModelSummary[]>> => {
    const response = await apiClient.get<ApiResponse<RegisteredModelSummary[]>>("/models", { params });
    return response.data;
  },

  getModelDetail: async (modelId: string): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>(`/models/${encodeURIComponent(modelId)}`);
    return response.data;
  },

  getModelMetrics: async (modelId: string): Promise<ApiResponse<ModelMetricsResponse>> => {
    const response = await apiClient.get<ApiResponse<ModelMetricsResponse>>(`/models/${encodeURIComponent(modelId)}/metrics`);
    return response.data;
  },

  getModelRuns: async (modelId: string): Promise<ApiResponse<MultiSeedRunsResponse>> => {
    const response = await apiClient.get<ApiResponse<MultiSeedRunsResponse>>(`/models/${encodeURIComponent(modelId)}/runs`);
    return response.data;
  },

  getModelArtifacts: async (modelId: string): Promise<ApiResponse<ModelArtifactsResponse>> => {
    const response = await apiClient.get<ApiResponse<ModelArtifactsResponse>>(`/models/${encodeURIComponent(modelId)}/artifacts`);
    return response.data;
  },

  getModelPromotion: async (modelId: string): Promise<ApiResponse<PromotionDecisionResponse>> => {
    const response = await apiClient.get<ApiResponse<PromotionDecisionResponse>>(`/models/${encodeURIComponent(modelId)}/promotion`);
    return response.data;
  },

  getModelExplanations: async (modelId: string): Promise<ApiResponse<ModelExplanationResponse>> => {
    const response = await apiClient.get<ApiResponse<ModelExplanationResponse>>(`/models/${encodeURIComponent(modelId)}/explanations`);
    return response.data;
  },
};

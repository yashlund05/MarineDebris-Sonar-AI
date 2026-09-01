import { apiClient } from "./client";
import { ApiResponse, Survey } from "../types";

export interface SurveyUploadResponse {
  survey_id: string;
  job_id: string;
  status: string;
  source_filename: string;
  file_size_bytes: number;
  created_at: string;
}

export interface ListSurveysParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export interface ReprocessSurveyPayload {
  detection_conf_threshold?: number;
  nms_iou_threshold?: number;
  run_segmentation?: boolean;
}

export const surveysApi = {
  uploadSurvey: async (
    file: File,
    navCsv?: File,
    channel: string = "starboard",
    onUploadProgress?: (progressEvent: any) => void
  ): Promise<ApiResponse<SurveyUploadResponse>> => {
    const formData = new FormData();
    formData.append("file", file);
    if (navCsv) {
      formData.append("nav_csv", navCsv);
    }
    formData.append("channel", channel);

    const response = await apiClient.post<ApiResponse<SurveyUploadResponse>>(
      "/surveys/upload",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress,
      }
    );
    return response.data;
  },

  getSurveys: async (params?: ListSurveysParams): Promise<ApiResponse<Survey[]>> => {
    const response = await apiClient.get<ApiResponse<Survey[]>>("/surveys", { params });
    return response.data;
  },

  getSurvey: async (surveyId: string): Promise<ApiResponse<Survey>> => {
    const response = await apiClient.get<ApiResponse<Survey>>(`/surveys/${surveyId}`);
    return response.data;
  },

  deleteSurvey: async (surveyId: string): Promise<ApiResponse<{ deleted: boolean }>> => {
    const response = await apiClient.delete<ApiResponse<{ deleted: boolean }>>(`/surveys/${surveyId}`);
    return response.data;
  },

  reprocessSurvey: async (
    surveyId: string,
    payload: ReprocessSurveyPayload
  ): Promise<ApiResponse<{ job_id: string; status: string }>> => {
    const response = await apiClient.post<ApiResponse<{ job_id: string; status: string }>>(
      `/surveys/${surveyId}/reprocess`,
      payload
    );
    return response.data;
  },

  getSonarImageUrl: (surveyId: string, channel: string = "starboard", mode: string = "raw"): string => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
    return `${baseUrl}/surveys/${surveyId}/sonar-image?channel=${channel}&mode=${mode}`;
  },
};

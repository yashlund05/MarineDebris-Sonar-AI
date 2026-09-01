import { apiClient } from "./client";
import { ApiResponse, Detection, DetectionClass } from "../types";

export interface ListDetectionsParams {
  job_id?: string;
  class_name?: DetectionClass;
  min_confidence?: number;
  include_filtered?: boolean;
  limit?: number;
  offset?: number;
}

export const detectionsApi = {
  getSurveyDetections: async (
    surveyId: string,
    params?: ListDetectionsParams
  ): Promise<ApiResponse<Detection[]>> => {
    const response = await apiClient.get<ApiResponse<Detection[]>>(
      `/surveys/${surveyId}/detections`,
      { params }
    );
    return response.data;
  },

  getDetection: async (detectionId: string): Promise<ApiResponse<Detection>> => {
    const response = await apiClient.get<ApiResponse<Detection>>(
      `/detections/${detectionId}`
    );
    return response.data;
  },
};

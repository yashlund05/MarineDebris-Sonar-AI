import { apiClient } from "./client";
import { ApiResponse, Report, ReportFormat } from "../types";

export interface GenerateReportPayload {
  format: ReportFormat;
  job_id?: string;
  min_confidence?: number;
  include_filtered?: boolean;
}

export interface GenerateReportResponse {
  report_id: string;
  format: ReportFormat;
  download_url: string;
}

export const reportsApi = {
  getSurveyReports: async (surveyId: string): Promise<ApiResponse<Report[]>> => {
    const response = await apiClient.get<ApiResponse<Report[]>>(`/surveys/${surveyId}/reports`);
    return response.data;
  },

  generateReport: async (
    surveyId: string,
    payload: GenerateReportPayload
  ): Promise<ApiResponse<GenerateReportResponse>> => {
    const response = await apiClient.post<ApiResponse<GenerateReportResponse>>(
      `/surveys/${surveyId}/reports/generate`,
      payload
    );
    return response.data;
  },

  getDownloadUrl: (reportId: string): string => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
    return `${baseUrl}/reports/${reportId}/download`;
  },
};

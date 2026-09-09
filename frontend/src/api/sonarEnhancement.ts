/**
 * API client for Sonar Enhancement & Visualization.
 */

import { apiClient } from "./client";
import {
  EnhancementResponse,
  SonarEnhancementConfig,
  PaletteItem,
  SampleItem,
} from "../types/sonarEnhancement";

export const sonarEnhancementApi = {
  getPalettes: async (): Promise<{ success: boolean; palettes: PaletteItem[] }> => {
    const res = await apiClient.get("/sonar/palettes");
    return res.data;
  },

  getSamples: async (
    datasetVersion: string = "v3",
    split: string = "val"
  ): Promise<{ success: boolean; samples: SampleItem[] }> => {
    const res = await apiClient.get("/sonar/samples", {
      params: { dataset_version: datasetVersion, split },
    });
    return res.data;
  },

  enhanceImage: async (
    payload: Partial<SonarEnhancementConfig> & {
      image_name?: string;
      survey_id?: string;
      image_data_url?: string;
      dataset_version?: string;
      split?: string;
    }
  ): Promise<EnhancementResponse> => {
    const res = await apiClient.post<EnhancementResponse>("/sonar/enhance", payload);
    return res.data;
  },

  enhanceUploadedFile: async (
    file: File,
    config: Partial<SonarEnhancementConfig>
  ): Promise<EnhancementResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    if (config.convert_to_db !== undefined) formData.append("convert_to_db", String(config.convert_to_db));
    if (config.stripe_noise_filter !== undefined) formData.append("stripe_noise_filter", String(config.stripe_noise_filter));
    if (config.clahe !== undefined) formData.append("clahe", String(config.clahe));
    if (config.clahe_clip_limit !== undefined) formData.append("clahe_clip_limit", String(config.clahe_clip_limit));
    if (config.sharpening !== undefined) formData.append("sharpening", String(config.sharpening));
    if (config.colormap) formData.append("colormap", config.colormap);
    if (config.run_detection !== undefined) formData.append("run_detection", String(config.run_detection));
    if (config.conf_threshold !== undefined) formData.append("conf_threshold", String(config.conf_threshold));
    if (config.detection_input_mode) formData.append("detection_input_mode", config.detection_input_mode);

    const res = await apiClient.post<EnhancementResponse>("/sonar/enhance/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  recolorCachedFrame: async (
    cacheKey: string,
    colormap: string
  ): Promise<{
    success: boolean;
    cache_key: string;
    colormap: string;
    pseudocolor_data_url: string;
    recolor_time_ms: number;
  }> => {
    const res = await apiClient.post("/sonar/recolor", {
      cache_key: cacheKey,
      colormap,
    });
    return res.data;
  },

  getDownloadUrl: (cacheKey: string, target: "raw" | "enhanced_gray" | "pseudocolor"): string => {
    const base = apiClient.defaults.baseURL || "/api/v1";
    return `${base}/sonar/download?cache_key=${encodeURIComponent(cacheKey)}&target=${target}`;
  },
};

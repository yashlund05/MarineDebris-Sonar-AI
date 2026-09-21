import { apiClient } from "./client";
import {
  EvidenceRecord,
  LiveHealthStatus,
  LiveSessionConfig,
  LiveSessionDetails,
  LiveTrack,
  LiveDetection,
  LiveMetrics,
} from "../features/live-sonar/types";

export const liveSonarApi = {
  // Create a new session
  createSession: async (config: LiveSessionConfig): Promise<LiveSessionDetails> => {
    const res = await apiClient.post<LiveSessionDetails>("/live-sonar/sessions", config);
    return res.data;
  },

  // List all registered sessions
  listSessions: async (): Promise<LiveSessionDetails[]> => {
    const res = await apiClient.get<LiveSessionDetails[]>("/live-sonar/sessions");
    return res.data;
  },

  // Get session status & metrics
  getSession: async (sessionId: string): Promise<LiveSessionDetails> => {
    const res = await apiClient.get<LiveSessionDetails>(`/live-sonar/sessions/${sessionId}`);
    return res.data;
  },

  // Start live session
  startSession: async (sessionId: string): Promise<{ status: string; session_id: string }> => {
    const res = await apiClient.post<{ status: string; session_id: string }>(
      `/live-sonar/sessions/${sessionId}/start`
    );
    return res.data;
  },

  // Stop live session
  stopSession: async (sessionId: string): Promise<{ status: string; session_id: string }> => {
    const res = await apiClient.post<{ status: string; session_id: string }>(
      `/live-sonar/sessions/${sessionId}/stop`
    );
    return res.data;
  },

  // Query live metrics
  getMetrics: async (sessionId: string): Promise<LiveMetrics> => {
    const res = await apiClient.get<LiveMetrics>(`/live-sonar/sessions/${sessionId}/metrics`);
    return res.data;
  },

  // Query active tracks
  getTracks: async (sessionId: string): Promise<LiveTrack[]> => {
    const res = await apiClient.get<LiveTrack[]>(`/live-sonar/sessions/${sessionId}/tracks`);
    return res.data;
  },

  // Query latest detections
  getDetections: async (sessionId: string): Promise<LiveDetection[]> => {
    const res = await apiClient.get<LiveDetection[]>(`/live-sonar/sessions/${sessionId}/detections`);
    return res.data;
  },

  // Get captured evidence items
  getEvidence: async (sessionId: string): Promise<EvidenceRecord[]> => {
    const res = await apiClient.get<EvidenceRecord[]>(`/live-sonar/sessions/${sessionId}/evidence`);
    return res.data;
  },

  // Manually capture evidence snapshot
  captureSnapshot: async (
    sessionId: string,
    trackId?: number
  ): Promise<{ status: string; evidence: EvidenceRecord }> => {
    const params = trackId !== undefined ? { track_id: trackId } : {};
    const res = await apiClient.post<{ status: string; evidence: EvidenceRecord }>(
      `/live-sonar/sessions/${sessionId}/snapshot`,
      null,
      { params }
    );
    return res.data;
  },

  // System health
  getHealth: async (): Promise<LiveHealthStatus> => {
    const res = await apiClient.get<LiveHealthStatus>("/live-sonar/health");
    return res.data;
  },
};

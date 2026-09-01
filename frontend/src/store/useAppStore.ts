import { create } from "zustand";
import { Detection, DetectionClass, Survey } from "../types";

interface AppState {
  // Selected survey
  activeSurveyId: string | null;
  activeSurvey: Survey | null;
  setActiveSurvey: (survey: Survey | null) => void;

  // Selected detection
  selectedDetection: Detection | null;
  setSelectedDetection: (detection: Detection | null) => void;

  // Filters
  selectedClass: DetectionClass | "all";
  setSelectedClass: (className: DetectionClass | "all") => void;

  minConfidence: number;
  setMinConfidence: (val: number) => void;

  includeFiltered: boolean;
  setIncludeFiltered: (val: boolean) => void;

  // Sonar viewer controls
  sonarMode: "raw" | "processed";
  setSonarMode: (mode: "raw" | "processed") => void;

  sonarChannel: "port" | "starboard";
  setSonarChannel: (channel: "port" | "starboard") => void;

  showOverlay: boolean;
  setShowOverlay: (show: boolean) => void;

  // Detail Modal
  isDetectionModalOpen: boolean;
  setDetectionModalOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeSurveyId: null,
  activeSurvey: null,
  setActiveSurvey: (survey) => set({ activeSurvey: survey, activeSurveyId: survey ? survey.id : null }),

  selectedDetection: null,
  setSelectedDetection: (detection) =>
    set({ selectedDetection: detection, isDetectionModalOpen: detection !== null }),

  selectedClass: "all",
  setSelectedClass: (className) => set({ selectedClass: className }),

  minConfidence: 0.35,
  setMinConfidence: (val) => set({ minConfidence: val }),

  includeFiltered: false,
  setIncludeFiltered: (val) => set({ includeFiltered: val }),

  sonarMode: "processed",
  setSonarMode: (mode) => set({ sonarMode: mode }),

  sonarChannel: "starboard",
  setSonarChannel: (channel) => set({ sonarChannel: channel }),

  showOverlay: true,
  setShowOverlay: (show) => set({ showOverlay: show }),

  isDetectionModalOpen: false,
  setDetectionModalOpen: (open) => set({ isDetectionModalOpen: open }),
}));

import { DetectionClass } from "../types";

export interface ClassColorMeta {
  color: string;
  bg: string;
  border: string;
  text: string;
  label: string;
}

export const CLASS_COLORS: Record<DetectionClass, ClassColorMeta> = {
  derelict_fishing_gear: {
    color: "#F59E0B",
    bg: "rgba(245, 158, 11, 0.15)",
    border: "#F59E0B",
    text: "#FBBF24",
    label: "Derelict Fishing Gear",
  },
  general_marine_debris: {
    color: "#EF4444",
    bg: "rgba(239, 68, 68, 0.15)",
    border: "#EF4444",
    text: "#F87171",
    label: "General Marine Debris",
  },
  shipwreck: {
    color: "#8B5CF6",
    bg: "rgba(139, 92, 246, 0.15)",
    border: "#8B5CF6",
    text: "#A78BFA",
    label: "Shipwreck",
  },
  pipe_or_cylinder: {
    color: "#06B6D4",
    bg: "rgba(6, 182, 212, 0.15)",
    border: "#06B6D4",
    text: "#22D3EE",
    label: "Pipe / Cylinder",
  },
  other_man_made_target: {
    color: "#84CC16",
    bg: "rgba(132, 204, 22, 0.15)",
    border: "#84CC16",
    text: "#A3E635",
    label: "Other Man-Made Target",
  },
  natural_feature: {
    color: "#6B7280",
    bg: "rgba(107, 114, 128, 0.15)",
    border: "#6B7280",
    text: "#9CA3AF",
    label: "Natural Feature (Audit)",
  },
};

export function getClassColor(className: DetectionClass): ClassColorMeta {
  return CLASS_COLORS[className] || CLASS_COLORS.natural_feature;
}

export function formatConfidence(score?: number): string {
  if (score === undefined || score === null) return "N/A";
  return `${(score * 100).toFixed(1)}%`;
}

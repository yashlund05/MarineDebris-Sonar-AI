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
    color: "#D97706",
    bg: "#FEF3C7",
    border: "#F59E0B",
    text: "#92400E",
    label: "Derelict Fishing Gear",
  },
  general_marine_debris: {
    color: "#DC2626",
    bg: "#FEE2E2",
    border: "#EF4444",
    text: "#991B1B",
    label: "General Marine Debris",
  },
  shipwreck: {
    color: "#7C3AED",
    bg: "#EDE9FE",
    border: "#8B5CF6",
    text: "#5B21B6",
    label: "Shipwreck",
  },
  pipe_or_cylinder: {
    color: "#0891B2",
    bg: "#CFFAFE",
    border: "#06B6D4",
    text: "#155E75",
    label: "Pipe / Cylinder",
  },
  other_man_made_target: {
    color: "#16A34A",
    bg: "#DCFCE7",
    border: "#22C55E",
    text: "#166534",
    label: "Other Man-Made Target",
  },
  natural_feature: {
    color: "#475569",
    bg: "#F1F5F9",
    border: "#CBD5E1",
    text: "#334155",
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

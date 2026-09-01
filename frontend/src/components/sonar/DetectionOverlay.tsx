import React from "react";
import { Detection } from "../../types";
import { getClassColor, formatConfidence } from "../../utils/classColors";
import { useAppStore } from "../../store/useAppStore";

interface DetectionOverlayProps {
  detections: Detection[];
  imageWidth: number;
  imageHeight: number;
}

export const DetectionOverlay: React.FC<DetectionOverlayProps> = ({
  detections,
  imageWidth,
  imageHeight,
}) => {
  const {
    selectedDetection,
    setSelectedDetection,
    selectedClass,
    minConfidence,
    includeFiltered,
  } = useAppStore();

  const filteredDetections = detections.filter((d) => {
    if (selectedClass !== "all" && d.class_name !== selectedClass) return false;
    if (d.confidence < minConfidence) return false;
    if (!includeFiltered && d.is_filtered) return false;
    return true;
  });

  return (
    <svg
      className="absolute top-0 left-0 pointer-events-none"
      style={{ width: imageWidth, height: imageHeight }}
      viewBox={`0 0 ${imageWidth} ${imageHeight}`}
    >
      {filteredDetections.map((det) => {
        const meta = getClassColor(det.class_name);
        const isSelected = selectedDetection?.id === det.id;

        return (
          <g
            key={det.id}
            className="cursor-pointer pointer-events-auto group"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedDetection(det);
            }}
          >
            {/* Detection Bounding Box */}
            <rect
              x={det.bbox_x}
              y={det.bbox_y}
              width={det.bbox_w}
              height={det.bbox_h}
              fill={isSelected ? `${meta.color}30` : `${meta.color}15`}
              stroke={isSelected ? "#FFFFFF" : meta.color}
              strokeWidth={isSelected ? 3 : 2}
              strokeDasharray={det.is_filtered ? "4 2" : "none"}
              className="transition-all duration-150"
            />

            {/* Label tag */}
            <g
              transform={`translate(${det.bbox_x}, ${Math.max(
                det.bbox_y - 20,
                0
              )})`}
            >
              <rect
                x={0}
                y={0}
                width={Math.max(det.bbox_w, 100)}
                height={18}
                fill="#0A0E14"
                stroke={meta.color}
                strokeWidth={1}
                rx={3}
                opacity={0.9}
              />
              <text
                x={4}
                y={13}
                fill={meta.text}
                fontSize={10}
                fontFamily="JetBrains Mono, monospace"
                fontWeight="bold"
              >
                {meta.label.slice(0, 14)} {formatConfidence(det.confidence_calibrated || det.confidence)}
              </text>
            </g>
          </g>
        );
      })}
    </svg>
  );
};

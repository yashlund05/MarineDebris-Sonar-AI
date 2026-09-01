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
    showDetections,
    showSegmentation,
    showClassification,
    showConfidence,
    showGeolocation,
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

        const hasSeg = det.segmentation?.status === "available";
        const hasClassif = det.classification?.status === "available";

        // Label text construction
        let tagText = meta.label;
        if (showConfidence) {
          tagText += ` ${formatConfidence(det.confidence_calibrated || det.confidence)}`;
        }
        if (showClassification && hasClassif) {
          tagText += ` • ${det.classification?.model || "Clf"}:${det.classification?.agreement ? "✓" : "⚠"}`;
        }
        if (showGeolocation && det.latitude && det.longitude) {
          tagText += ` • [${det.latitude.toFixed(3)}, ${det.longitude.toFixed(3)}]`;
        }

        return (
          <g
            key={det.id}
            className="cursor-pointer pointer-events-auto"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedDetection(det);
            }}
          >
            {/* Detection Bounding Box - Thin professional outline */}
            {showDetections && (
              <rect
                x={det.bbox_x}
                y={det.bbox_y}
                width={det.bbox_w}
                height={det.bbox_h}
                fill={isSelected ? `${meta.color}25` : `${meta.color}08`}
                stroke={isSelected ? "#FFFFFF" : meta.color}
                strokeWidth={isSelected ? 2.5 : 1.5}
                strokeDasharray={det.is_filtered ? "4 3" : "none"}
                rx={2}
              />
            )}

            {/* Corner Indicators for Selected Target */}
            {isSelected && showDetections && (
              <g stroke="#FFFFFF" strokeWidth={2} fill="none">
                <path d={`M ${det.bbox_x - 3} ${det.bbox_y + 6} L ${det.bbox_x - 3} ${det.bbox_y - 3} L ${det.bbox_x + 6} ${det.bbox_y - 3}`} />
                <path d={`M ${det.bbox_x + det.bbox_w + 3} ${det.bbox_y + 6} L ${det.bbox_x + det.bbox_w + 3} ${det.bbox_y - 3} L ${det.bbox_x + det.bbox_w - 6} ${det.bbox_y - 3}`} />
                <path d={`M ${det.bbox_x - 3} ${det.bbox_y + det.bbox_h - 6} L ${det.bbox_x - 3} ${det.bbox_y + det.bbox_h + 3} L ${det.bbox_x + 6} ${det.bbox_y + det.bbox_h + 3}`} />
                <path d={`M ${det.bbox_x + det.bbox_w + 3} ${det.bbox_y + det.bbox_h - 6} L ${det.bbox_x + det.bbox_w + 3} ${det.bbox_y + det.bbox_h + 3} L ${det.bbox_x + det.bbox_w - 6} ${det.bbox_y + det.bbox_h + 3}`} />
              </g>
            )}

            {/* Segmentation Mask Overlay */}
            {showSegmentation && hasSeg && (
              <rect
                x={det.bbox_x + 2}
                y={det.bbox_y + 2}
                width={Math.max(0, det.bbox_w - 4)}
                height={Math.max(0, det.bbox_h - 4)}
                fill="#9333EA25"
                stroke="#A855F7"
                strokeWidth={1.5}
                rx={3}
              />
            )}

            {/* Label tag - Clean small solid badge */}
            <g
              transform={`translate(${det.bbox_x}, ${Math.max(
                det.bbox_y - 18,
                0
              )})`}
            >
              <rect
                x={0}
                y={0}
                width={Math.max(det.bbox_w, tagText.length * 6.2 + 10)}
                height={16}
                fill="#0F172A"
                stroke={isSelected ? "#FFFFFF" : meta.color}
                strokeWidth={1}
                rx={3}
                opacity={0.92}
              />
              <text
                x={4}
                y={11.5}
                fill="#F8FAFC"
                fontSize={9.5}
                fontFamily="JetBrains Mono, monospace"
                fontWeight="600"
              >
                {tagText}
              </text>
            </g>
          </g>
        );
      })}
    </svg>
  );
};

export default DetectionOverlay;

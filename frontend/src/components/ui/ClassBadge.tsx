import React from "react";
import { DetectionClass } from "../../types";
import { getClassColor } from "../../utils/classColors";

interface ClassBadgeProps {
  className: DetectionClass;
  size?: "sm" | "md";
}

export const ClassBadge: React.FC<ClassBadgeProps> = ({ className, size = "md" }) => {
  const meta = getClassColor(className);

  const sizeClasses =
    size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs font-medium";

  return (
    <span
      className={`inline-flex items-center rounded-full font-mono tracking-wide ${sizeClasses}`}
      style={{
        backgroundColor: meta.bg,
        color: meta.text,
        border: `1px solid ${meta.border}40`,
      }}
    >
      <span
        className="mr-1.5 h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: meta.color }}
      />
      {meta.label}
    </span>
  );
};

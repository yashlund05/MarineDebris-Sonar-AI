import React from "react";
import { Filter, SlidersHorizontal } from "lucide-react";
import { DetectionClass } from "../../types";
import { useAppStore } from "../../store/useAppStore";

export const FilterBar: React.FC = () => {
  const {
    selectedClass,
    setSelectedClass,
    minConfidence,
    setMinConfidence,
    includeFiltered,
    setIncludeFiltered,
  } = useAppStore();

  const classList: { id: DetectionClass | "all"; label: string }[] = [
    { id: "all", label: "All Classes" },
    { id: "derelict_fishing_gear", label: "Fishing Gear" },
    { id: "general_marine_debris", label: "General Debris" },
    { id: "shipwreck", label: "Shipwreck" },
    { id: "pipe_or_cylinder", label: "Pipe / Cylinder" },
    { id: "other_man_made_target", label: "Other Target" },
    { id: "natural_feature", label: "Natural Feature" },
  ];

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-bg-surface border border-border-subtle rounded-xl shadow-subtle">
      <div className="flex flex-wrap items-center gap-1.5">
        <div className="flex items-center text-xs font-semibold text-text-muted mr-1 font-mono text-[11px]">
          <Filter className="w-3.5 h-3.5 mr-1 text-accent" />
          Filter:
        </div>
        {classList.map((item) => {
          const isSelected = selectedClass === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelectedClass(item.id)}
              className={`px-2.5 py-1 text-xs rounded-lg transition-all font-medium border cursor-pointer ${
                isSelected
                  ? "bg-accent text-white border-accent shadow-xs font-semibold"
                  : "bg-slate-50 text-text-secondary border-border-subtle hover:bg-slate-100 hover:text-text-primary"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-secondary flex items-center font-mono text-[11px]">
            <SlidersHorizontal className="w-3.5 h-3.5 mr-1 text-accent" />
            Min Conf:
          </span>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-24 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-accent"
          />
          <span className="font-mono text-xs font-bold text-text-primary w-8">
            {Math.round(minConfidence * 100)}%
          </span>
        </div>

        <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer hover:text-text-primary font-medium select-none">
          <input
            type="checkbox"
            checked={includeFiltered}
            onChange={(e) => setIncludeFiltered(e.target.checked)}
            className="rounded border-border-default text-accent focus:ring-accent w-3.5 h-3.5"
          />
          Show Filtered
        </label>
      </div>
    </div>
  );
};

export default FilterBar;

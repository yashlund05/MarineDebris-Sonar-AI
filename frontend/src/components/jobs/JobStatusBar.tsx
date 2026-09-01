import React from "react";
import { CheckCircle2, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { useJobProgress } from "../../hooks/useJobProgress";

interface JobStatusBarProps {
  jobId?: string;
  initialStatus?: string;
  initialProgress?: number;
  initialStage?: string;
}

const PIPELINE_STAGES = [
  { id: "INGEST", label: "Ingest", minPct: 5 },
  { id: "PREPROCESS", label: "Preprocess", minPct: 20 },
  { id: "TILE", label: "Tile", minPct: 35 },
  { id: "DETECT", label: "Detect", minPct: 50 },
  { id: "FILTER", label: "Filter", minPct: 65 },
  { id: "SEGMENT", label: "Segment", minPct: 75, note: "Optional/Degraded" },
  { id: "CLASSIFY", label: "Classify", minPct: 82, note: "Optional/Degraded" },
  { id: "GEOREFERENCE", label: "Georef", minPct: 90 },
  { id: "PERSIST", label: "Persist", minPct: 95 },
  { id: "REPORT", label: "Report", minPct: 99 },
];

export const JobStatusBar: React.FC<JobStatusBarProps> = ({
  jobId,
  initialStatus = "pending",
  initialProgress = 0,
  initialStage = "Queued",
}) => {
  const { progress } = useJobProgress(jobId);

  const status = progress?.status || initialStatus;
  const progressPct = progress?.progress_pct ?? initialProgress;
  const stage = progress?.current_stage || initialStage;

  if (status === "complete") {
    return (
      <div className="bg-bg-surface border border-emerald-200 rounded-2xl p-4 shadow-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Acoustic Processing Complete</span>
            <span className="text-emerald-700/80 font-normal">
              — All candidate targets preprocessed, filtered, and georeferenced
            </span>
          </div>
          <span className="font-mono text-xs font-bold text-emerald-800">100%</span>
        </div>

        {/* Completed Pipeline Flow */}
        <div className="flex flex-wrap items-center gap-1.5 p-2 bg-slate-50 border border-border-subtle rounded-xl text-[10px] font-mono">
          {PIPELINE_STAGES.map((s, idx) => (
            <React.Fragment key={s.id}>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold border border-emerald-200">
                ✓ {s.label}
              </span>
              {idx < PIPELINE_STAGES.length - 1 && <ArrowRight className="w-3 h-3 text-slate-300" />}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="flex items-center justify-between p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 shadow-card">
        <div className="flex items-center gap-2 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 text-rose-600" />
          <span>Processing Interrupted:</span>
          <span className="text-rose-700 font-normal">{stage}</span>
        </div>
        <span className="font-mono text-xs font-bold text-rose-800">Failed</span>
      </div>
    );
  }

  return (
    <div className="p-4 bg-bg-surface border border-border-subtle rounded-2xl space-y-3 shadow-card">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 font-medium text-text-primary">
          <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" />
          <span className="text-text-muted">Current Pipeline Stage:</span>
          <span className="text-accent font-bold font-mono">{stage}</span>
        </div>
        <span className="font-mono text-xs font-bold text-text-primary">
          {progressPct}%
        </span>
      </div>

      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-border-subtle">
        <div
          className="bg-accent h-full transition-all duration-300 rounded-full"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Live Pipeline Flow */}
      <div className="flex flex-wrap items-center gap-1.5 pt-0.5 text-[10px] font-mono">
        {PIPELINE_STAGES.map((s, idx) => {
          const isDone = progressPct >= s.minPct;
          const isCurrent = progressPct < s.minPct && (idx === 0 || progressPct >= PIPELINE_STAGES[idx - 1].minPct);
          return (
            <React.Fragment key={s.id}>
              <span
                className={`px-2 py-0.5 rounded transition-all border ${
                  isDone
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold"
                    : isCurrent
                    ? "bg-sky-50 text-sky-800 border-sky-300 font-bold"
                    : "bg-slate-50 text-text-muted border-border-subtle"
                }`}
              >
                {isDone ? `✓ ${s.label}` : s.label}
              </span>
              {idx < PIPELINE_STAGES.length - 1 && <ArrowRight className="w-3 h-3 text-slate-300" />}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default JobStatusBar;

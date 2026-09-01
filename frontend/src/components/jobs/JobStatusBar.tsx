import React from "react";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useJobProgress } from "../../hooks/useJobProgress";

interface JobStatusBarProps {
  jobId?: string;
  initialStatus?: string;
  initialProgress?: number;
  initialStage?: string;
}

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
      <div className="flex items-center justify-between p-3 px-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-400">
        <div className="flex items-center gap-2 text-sm font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Processing Complete</span>
          <span className="text-xs text-emerald-500/80">— All detections analyzed and georeferenced</span>
        </div>
        <span className="font-mono text-xs font-semibold">100%</span>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="flex items-center justify-between p-3 px-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400">
        <div className="flex items-center gap-2 text-sm font-medium">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span>Processing Failed</span>
          <span className="text-xs text-red-500/80">— {stage}</span>
        </div>
        <span className="font-mono text-xs font-semibold">Failed</span>
      </div>
    );
  }

  return (
    <div className="p-3.5 px-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 font-medium text-text-primary">
          <Loader2 className="w-3.5 h-3.5 text-accent animate-spin" />
          <span>Pipeline Stage:</span>
          <span className="text-accent font-semibold">{stage}</span>
        </div>
        <span className="font-mono text-xs font-semibold text-text-secondary">
          {progressPct}%
        </span>
      </div>

      <div className="w-full bg-bg-elevated h-2 rounded-full overflow-hidden">
        <div
          className="bg-accent h-full transition-all duration-300 rounded-full"
          style={{ width: `${progressPct}%` }}
        />
      </div>
    </div>
  );
};

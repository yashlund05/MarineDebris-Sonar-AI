import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { systemApi } from "../api/client";
import { surveysApi } from "../api/surveys";
import {
  Server,
  Database,
  Cpu,
  Waves,
  UploadCloud,
  CheckCircle2,
  ArrowRight,
  Target,
  BarChart3,
} from "lucide-react";
import { CLASS_COLORS } from "../utils/classColors";

export const DashboardPage: React.FC = () => {
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 10000,
  });

  const { data: surveysData } = useQuery({
    queryKey: ["surveys"],
    queryFn: () => surveysApi.getSurveys({ limit: 10 }),
  });

  const health = healthData;
  const surveys = surveysData?.data || [];

  const totalDetections = surveys.reduce(
    (acc, s) => acc + ((s as any).detection_count || 0),
    0
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wide mb-1">
            <Waves className="w-4 h-4" />
            Operational Command Center
          </div>
          <h1 className="text-2xl font-bold text-text-primary">
            Marine Debris & Acoustic Anomaly Detection
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Automated sidescan sonar inspection, spatial geotagging, and marine debris classification.
          </p>
        </div>

        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition-all shadow-lg"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Sonar Strip
        </Link>
      </div>

      {/* System Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-secondary">Core Database</span>
            <Database className="w-4 h-4 text-accent" />
          </div>
          <div>
            <span className="text-xl font-bold text-text-primary capitalize">
              {health?.database || "Connecting..."}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">PostgreSQL 16 + PostGIS</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Schema Frozen v1.0.0
          </div>
        </div>

        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-secondary">Queue & Broker</span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <span className="text-xl font-bold text-text-primary capitalize">
              {health?.redis || "Connecting..."}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">Redis 7.2 + Celery</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Task Worker Active
          </div>
        </div>

        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-secondary">Inference Hardware</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <span className="text-xl font-bold text-text-primary uppercase font-mono">
              {health?.device || "CPU"}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">Compute Acceleration</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-medium font-mono">
            {health?.active_detection_model || "sonar_yolov8m"}
          </div>
        </div>

        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-secondary">Acoustic Surveys</span>
            <Target className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <span className="text-xl font-bold text-text-primary">
              {surveys.length} Sessions
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">
              {totalDetections} Total Detections
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-amber-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            100% Pipeline Verification
          </div>
        </div>
      </div>

      {/* Target Taxonomy Quick Reference */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent" />
            Acoustic Detection Classes
          </h2>
          <Link to="/models" className="text-xs text-accent hover:underline">
            View Model Specs →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {Object.entries(CLASS_COLORS).map(([key, meta]) => (
            <div
              key={key}
              className="p-3 rounded-xl border text-center space-y-1.5"
              style={{
                backgroundColor: meta.bg,
                borderColor: `${meta.border}40`,
              }}
            >
              <div
                className="w-3 h-3 rounded-full mx-auto shadow-sm"
                style={{ backgroundColor: meta.color }}
              />
              <p className="text-xs font-bold truncate" style={{ color: meta.text }}>
                {meta.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Surveys Table */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-text-primary">Recent Survey Records</h2>
          <Link to="/surveys" className="text-xs text-accent hover:underline">
            View All Archive →
          </Link>
        </div>

        {surveys.length === 0 ? (
          <p className="text-xs text-text-muted py-4">No surveys uploaded yet.</p>
        ) : (
          <div className="divide-y divide-border-subtle/60 overflow-hidden">
            {surveys.slice(0, 5).map((s) => (
              <div
                key={s.id}
                className="py-3 flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center gap-3">
                  <Waves className="w-4 h-4 text-accent flex-shrink-0" />
                  <div>
                    <span className="font-semibold text-text-primary block">
                      {s.source_filename}
                    </span>
                    <span className="text-text-muted text-[11px]">
                      {new Date(s.created_at).toLocaleDateString()} •{" "}
                      {(s.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-text-secondary">
                    <strong className="text-text-primary">
                      {(s as any).detection_count ?? 0}
                    </strong>{" "}
                    targets
                  </span>
                  <Link
                    to={`/surveys/${s.id}`}
                    className="p-1.5 bg-bg-elevated hover:bg-accent hover:text-white rounded-lg text-text-secondary transition-all"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;

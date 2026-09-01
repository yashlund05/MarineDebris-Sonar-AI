import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { surveysApi } from "../api/surveys";
import {
  Database,
  Cpu,
  Waves,
  UploadCloud,
  ArrowRight,
  Target,
  Layers,
  ChevronRight,
} from "lucide-react";

export const DashboardPage: React.FC = () => {
  const { data: surveysData } = useQuery({
    queryKey: ["surveys"],
    queryFn: () => surveysApi.getSurveys({ limit: 10 }),
  });

  const surveys = surveysData?.data || [];

  const totalDetections = surveys.reduce(
    (acc, s) => acc + ((s as any).detection_count || 0),
    0
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Section / Hero Banner */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sky-50 text-sky-800 border border-sky-200 text-xs font-semibold font-mono">
            <Waves className="w-3.5 h-3.5" />
            Forward-Looking Sonar (FLS) Operations
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Marine Debris Intelligence Platform
          </h1>
          <p className="text-sm text-text-secondary leading-relaxed">
            Automated acoustic anomaly detection, high-resolution FLS tiling, physical dimension estimation, and spatial georeferencing for underwater maritime surveys.
          </p>
        </div>

        <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 flex-shrink-0">
          <Link
            to="/upload"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition-all shadow-sm cursor-pointer"
          >
            <UploadCloud className="w-4 h-4" />
            New Sonar Analysis
          </Link>
          <Link
            to="/surveys"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-bg-surface hover:bg-bg-elevated border border-border-default text-text-primary text-xs font-semibold rounded-xl transition-all"
          >
            View Surveys
            <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Surveys */}
        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted uppercase tracking-wider font-mono">
            <span>Total Surveys</span>
            <Database className="w-4 h-4 text-accent" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {surveys.length}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">Stored in local survey catalog</p>
          </div>
          <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px]">
            <span className="text-emerald-700 font-medium">● Storage active</span>
            <Link to="/surveys" className="text-accent hover:underline flex items-center gap-0.5">
              Browse <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Sonar Images Processed */}
        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted uppercase tracking-wider font-mono">
            <span>Acoustic Strips</span>
            <Waves className="w-4 h-4 text-sky-600" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {surveys.length}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">Waterfall strips preprocessed</p>
          </div>
          <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px]">
            <span className="text-text-secondary font-mono">CLAHE + Denoised</span>
            <span className="text-text-muted">640×640 tiles</span>
          </div>
        </div>

        {/* Total Detections */}
        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted uppercase tracking-wider font-mono">
            <span>Verified Detections</span>
            <Target className="w-4 h-4 text-rose-600" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {totalDetections}
            </span>
            <p className="text-[11px] text-text-muted mt-0.5">Across active survey sessions</p>
          </div>
          <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px]">
            <span className="text-text-secondary">Spatial geotagged</span>
            <span className="text-text-muted font-mono">WGS84</span>
          </div>
        </div>

        {/* Model Status */}
        <div className="p-5 bg-bg-surface border border-border-subtle rounded-2xl shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-medium text-text-muted uppercase tracking-wider font-mono">
            <span>Model Readiness</span>
            <Cpu className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-3">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-amber-800">
                PENDING_WEIGHTS
              </span>
            </div>
            <p className="text-[11px] text-text-muted mt-0.5">YOLOv8m Acoustic Detector</p>
          </div>
          <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-[11px]">
            <span className="text-amber-800 font-mono font-medium">EXPERIMENTAL</span>
            <Link to="/models" className="text-accent hover:underline flex items-center gap-0.5">
              Model Center <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Recent Surveys + Dataset Quick Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Surveys Table */}
        <div className="lg:col-span-2 bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-accent" />
              <h2 className="text-base font-bold text-text-primary">Recent Sonar Surveys</h2>
            </div>
            <Link
              to="/surveys"
              className="text-xs text-accent hover:underline font-semibold flex items-center gap-1"
            >
              View all ({surveys.length}) <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {surveys.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-border-subtle rounded-xl bg-bg-elevated/30">
              <p className="text-xs text-text-muted">No surveys uploaded yet.</p>
              <Link
                to="/upload"
                className="mt-2 inline-block text-xs text-accent hover:underline font-semibold"
              >
                Upload your first acoustic survey
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-bg-elevated text-text-secondary uppercase tracking-wider font-mono text-[11px]">
                  <tr>
                    <th className="py-2.5 px-3 rounded-l-lg">Filename</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Detections</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 rounded-r-lg text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {surveys.slice(0, 5).map((s) => (
                    <tr key={s.id} className="hover:bg-bg-elevated/50 transition-colors">
                      <td className="py-3 px-3 font-semibold text-text-primary">
                        <Link to={`/surveys/${s.id}`} className="hover:text-accent truncate block max-w-xs">
                          {s.source_filename}
                        </Link>
                      </td>
                      <td className="py-3 px-3 font-mono text-text-secondary uppercase">
                        {s.file_type}
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-text-primary">
                        {(s as any).detection_count || 0}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                            s.status === "complete"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : s.status === "failed"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-sky-50 text-sky-700 border border-sky-200"
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link
                          to={`/surveys/${s.id}`}
                          className="inline-flex items-center gap-1 text-accent font-semibold hover:underline"
                        >
                          Inspect <ChevronRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Dataset & Acoustic Target Taxonomy */}
        <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent" />
              <h2 className="text-base font-bold text-text-primary">Acoustic Taxonomy</h2>
            </div>
            <Link to="/dataset" className="text-xs text-accent hover:underline font-semibold">
              Dataset Info
            </Link>
          </div>

          <p className="text-xs text-text-secondary leading-relaxed">
            Target categories recognized by the MarineDebris-Sonar-AI detection pipeline:
          </p>

          <div className="space-y-2 pt-1">
            <div className="p-3 bg-emerald-50/50 border border-emerald-200/80 rounded-xl space-y-1">
              <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider font-mono">
                ✓ Trained FLS Classes
              </div>
              <div className="space-y-1 text-xs text-text-primary">
                <div className="flex justify-between font-mono">
                  <span>general_marine_debris</span>
                  <span className="font-semibold text-emerald-700">267 boxes</span>
                </div>
                <div className="flex justify-between font-mono">
                  <span>other_man_made_target</span>
                  <span className="font-semibold text-emerald-700">104 boxes</span>
                </div>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl space-y-1">
              <div className="text-[11px] font-bold text-text-muted uppercase tracking-wider font-mono">
                — Untrained Canonical Classes
              </div>
              <div className="space-y-1 text-xs text-text-muted font-mono">
                <div className="flex justify-between">
                  <span>derelict_fishing_gear</span>
                  <span>0 samples</span>
                </div>
                <div className="flex justify-between">
                  <span>shipwreck</span>
                  <span>0 samples</span>
                </div>
                <div className="flex justify-between">
                  <span>pipe_or_cylinder</span>
                  <span>0 samples</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

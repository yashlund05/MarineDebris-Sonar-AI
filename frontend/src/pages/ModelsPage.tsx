import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Cpu,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Tag,
  Database,
  Layers,
  Activity,
  ShieldAlert,
} from "lucide-react";
import { modelsApi } from "../api/models";
import { ModelRegistryItem } from "../types";
import { TableSkeleton } from "../components/ui/Skeleton";

export const ModelsPage: React.FC = () => {
  const { data: modelsData, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.getModels(),
  });

  const models = modelsData?.data || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Title & Subtitle */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider font-mono mb-1">
          <Cpu className="w-3.5 h-3.5" />
          Acoustic AI Infrastructure
        </div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          Model Center & Acoustic AI Registry
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Truthful catalog of acoustic object detectors, semantic segmenters, and secondary candidate classifiers.
        </p>
      </div>

      {/* Model Readiness Gate & Anti-Fabrication Certification */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4">
          <div className="flex items-center gap-2.5">
            <Activity className="w-5 h-5 text-accent" />
            <h2 className="text-base font-bold text-text-primary">
              Production AI Readiness & Quality Gate
            </h2>
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 rounded-full text-xs font-semibold font-mono">
            <AlertTriangle className="w-3.5 h-3.5" />
            ML-WEIGHTS-BLOCKED
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-1">
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">Acoustic Dataset</span>
            <div className="flex items-center gap-1.5 text-emerald-800 font-bold text-xs mt-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              VALIDATED
            </div>
          </div>
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">YOLOv8m Weights</span>
            <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs mt-2">
              <XCircle className="w-4 h-4 text-rose-600" />
              MISSING_WEIGHTS
            </div>
          </div>
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">Live Inference</span>
            <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs mt-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              PENDING_TRAIN
            </div>
          </div>
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">U-Net Segmenter</span>
            <div className="flex items-center gap-1.5 text-text-muted font-bold text-xs mt-2">
              <XCircle className="w-4 h-4" />
              UNAVAILABLE
            </div>
          </div>
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">MobileNet Classifier</span>
            <div className="flex items-center gap-1.5 text-text-muted font-bold text-xs mt-2">
              <XCircle className="w-4 h-4" />
              UNAVAILABLE
            </div>
          </div>
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex flex-col justify-between">
            <span className="text-[11px] text-text-muted font-mono">Production Status</span>
            <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs mt-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              EXPERIMENTAL
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Provenance & Supported Classes Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
            <Database className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-bold text-text-primary">
              Accepted FLS Benchmark
            </h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            University of Groningen / Heriot-Watt benchmark captured via ARIS Explorer 3000 (3.0 MHz high-frequency sonar).
          </p>

          <div className="space-y-2 pt-1 text-xs">
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Total Acoustic Images</span>
              <span className="font-mono font-bold text-text-primary">238</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Total Ground-Truth Boxes</span>
              <span className="font-mono font-bold text-text-primary">371</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Train Split (70%)</span>
              <span className="font-mono text-emerald-800 font-semibold">166 images (258 boxes)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Validation Split (15%)</span>
              <span className="font-mono text-sky-800 font-semibold">35 images (55 boxes)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Held-Out Test Split (15%)</span>
              <span className="font-mono text-purple-800 font-semibold">37 images (58 boxes)</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-text-muted">License / DOI</span>
              <span className="font-mono text-accent font-semibold">CC-BY 4.0 (10.5281/zenodo.15101686)</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-3">
            <div className="flex items-center gap-2">
              <Tag className="w-4 h-4 text-accent" />
              <h3 className="text-sm font-bold text-text-primary">
                Class Taxonomy & Training Scope
              </h3>
            </div>
            <span className="text-xs font-mono text-text-muted">2 Trained • 3 Untrained</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold uppercase tracking-wider font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Supported Trained Classes
              </div>
              <ul className="space-y-1.5 text-xs text-text-primary">
                <li className="flex items-center justify-between font-mono">
                  <span>general_marine_debris</span>
                  <span className="font-bold text-emerald-800">267 boxes</span>
                </li>
                <li className="flex items-center justify-between font-mono">
                  <span>other_man_made_target</span>
                  <span className="font-bold text-emerald-800">104 boxes</span>
                </li>
              </ul>
              <p className="text-[11px] text-text-muted pt-1">
                Validated targets: beverage cans, bottles, tires, submerged chains, valves, ship propellers.
              </p>
            </div>

            <div className="p-4 bg-slate-50 border border-border-subtle rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-rose-800 text-xs font-bold uppercase tracking-wider font-mono">
                <XCircle className="w-4 h-4 text-rose-600" />
                Untrained Canonical Classes
              </div>
              <ul className="space-y-1.5 text-xs text-text-muted font-mono">
                <li className="flex items-center justify-between">
                  <span>derelict_fishing_gear</span>
                  <span className="text-rose-700 font-semibold">0 samples</span>
                </li>
                <li className="flex items-center justify-between">
                  <span>shipwreck</span>
                  <span className="text-rose-700 font-semibold">0 samples</span>
                </li>
                <li className="flex items-center justify-between">
                  <span>pipe_or_cylinder</span>
                  <span className="text-rose-700 font-semibold">0 samples</span>
                </li>
              </ul>
              <p className="text-[11px] text-text-muted pt-1">
                Preserved in schema but explicitly gated to prevent unverified predictions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Models Catalog Table */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-accent" />
          <h3 className="text-sm font-bold text-text-primary">
            Registered Models Catalog
          </h3>
        </div>

        {isLoading ? (
          <TableSkeleton rows={4} cols={6} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-bg-elevated text-text-secondary uppercase tracking-wider font-mono text-[11px]">
                <tr>
                  <th className="py-3 px-4 rounded-l-lg font-semibold">Model Name</th>
                  <th className="py-3 px-4 font-semibold">Task</th>
                  <th className="py-3 px-4 font-semibold">Architecture</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Device</th>
                  <th className="py-3 px-4 font-semibold">Supported Classes</th>
                  <th className="py-3 px-4 rounded-r-lg font-semibold">Weights Path</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle font-mono">
                {models.map((m: ModelRegistryItem) => {
                  const isReady = m.status === "READY" || m.runtime_status === "READY";
                  return (
                    <tr key={m.id} className="hover:bg-bg-elevated/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-text-primary">
                        {m.model_name || m.name}
                        <span className="block text-[10px] text-text-muted font-normal">
                          v{m.version} • {m.framework || "PyTorch"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-accent font-semibold">{m.task}</td>
                      <td className="py-3 px-4 text-text-secondary">{m.architecture || "N/A"}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            isReady
                              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                              : "bg-rose-50 text-rose-800 border border-rose-200"
                          }`}
                        >
                          {isReady ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> : <XCircle className="w-3 h-3 text-rose-600" />}
                          {m.status || m.runtime_status || "MISSING_WEIGHTS"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-muted">{m.device || "CPU"}</td>
                      <td className="py-3 px-4 text-text-secondary text-[11px]">
                        {m.supported_classes ? m.supported_classes.join(", ") : "2 classes"}
                      </td>
                      <td className="py-3 px-4 text-[11px] text-text-muted truncate max-w-[200px]">
                        {m.weights_path || m.weight_path || "N/A"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelsPage;

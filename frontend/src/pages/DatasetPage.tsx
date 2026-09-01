import React from "react";
import {
  Database,
  Radio,
  FileCheck,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  BarChart2,
} from "lucide-react";

export const DatasetPage: React.FC = () => {
  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider font-mono mb-1">
          <Database className="w-3.5 h-3.5" />
          Acoustic Benchmark Catalog
        </div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          Marine Debris FLS Acoustic Dataset
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Standardized high-frequency Forward-Looking Sonar (FLS) acoustic dataset acquired via ARIS Explorer 3000.
        </p>
      </div>

      {/* Dataset Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sensor & Provenance */}
        <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
            <Radio className="w-4 h-4 text-accent" />
            <h2 className="text-sm font-bold text-text-primary">Acoustic Sensor & Source</h2>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Sonar Camera</span>
              <span className="font-mono font-semibold text-text-primary">ARIS Explorer 3000</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Operating Frequency</span>
              <span className="font-mono font-semibold text-accent">3.0 MHz (Identification)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Research Institution</span>
              <span className="text-text-primary">Univ. of Groningen / Heriot-Watt</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Principal Investigator</span>
              <span className="text-text-primary">Dr. Matias Valdenegro-Toro</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border-subtle">
              <span className="text-text-muted">Permanent DOI</span>
              <span className="font-mono text-accent">10.5281/zenodo.15101686</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-text-muted">Legal License</span>
              <span className="font-semibold text-emerald-700">CC-BY 4.0 International</span>
            </div>
          </div>
        </div>

        {/* Partition Statistics */}
        <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
            <FileCheck className="w-4 h-4 text-accent" />
            <h2 className="text-sm font-bold text-text-primary">Sequence-Split Distribution</h2>
          </div>

          <div className="space-y-3 pt-1">
            {/* Train Split */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="font-semibold text-text-primary">Train Split (70%)</span>
                <span className="text-emerald-700 font-bold">166 images • 258 boxes</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: "70%" }} />
              </div>
            </div>

            {/* Validation Split */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="font-semibold text-text-primary">Validation Split (15%)</span>
                <span className="text-sky-700 font-bold">35 images • 55 boxes</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-sky-500 h-full rounded-full" style={{ width: "15%" }} />
              </div>
            </div>

            {/* Test Split */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="font-semibold text-text-primary">Held-Out Test Split (15%)</span>
                <span className="text-purple-700 font-bold">37 images • 58 boxes</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-purple-500 h-full rounded-full" style={{ width: "15%" }} />
              </div>
            </div>

            <div className="pt-2 border-t border-border-subtle flex items-center justify-between text-xs font-mono">
              <span className="text-text-muted">Total Acoustic Frames:</span>
              <span className="font-bold text-text-primary">238 validated</span>
            </div>
          </div>
        </div>

        {/* Verification & Quality Audit */}
        <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-text-primary">Quality & Integrity Audit</h2>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200">
              <span className="font-medium">Sequence Independence</span>
              <span className="font-bold font-mono">0% LEAKAGE</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 text-text-secondary border border-border-subtle">
              <span>Standardized Canvas</span>
              <span className="font-mono font-semibold text-text-primary">640×640 px</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 text-text-secondary border border-border-subtle">
              <span>Annotation Format</span>
              <span className="font-mono font-semibold text-text-primary">YOLO Normalised</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 text-text-secondary border border-border-subtle">
              <span>Dataset Manifest</span>
              <span className="font-mono text-accent">DATASET_MANIFEST.json</span>
            </div>
          </div>
        </div>
      </div>

      {/* Class Distribution & Taxonomy Breakdown */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 sm:p-8 shadow-card space-y-6">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4">
          <div className="flex items-center gap-2.5">
            <BarChart2 className="w-5 h-5 text-accent" />
            <h2 className="text-base font-bold text-text-primary">
              Ground-Truth Class Distribution (371 Annotations)
            </h2>
          </div>
          <span className="text-xs font-mono text-text-muted">ARIS 3000 FLS Targets</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Supported Trained Targets */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-800 font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Supported Trained Classes (Current Dataset)
            </div>

            <div className="space-y-3">
              <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="font-bold text-text-primary">general_marine_debris</span>
                  <span className="font-bold text-emerald-800">267 boxes (72%)</span>
                </div>
                <div className="w-full bg-emerald-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-600 h-full rounded-full" style={{ width: "72%" }} />
                </div>
                <p className="text-[11px] text-text-muted">
                  Submerged beverage cans, plastic bottles, glass bottles, drink cartons, tires.
                </p>
              </div>

              <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="font-bold text-text-primary">other_man_made_target</span>
                  <span className="font-bold text-emerald-800">104 boxes (28%)</span>
                </div>
                <div className="w-full bg-emerald-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-600 h-full rounded-full" style={{ width: "28%" }} />
                </div>
                <p className="text-[11px] text-text-muted">
                  Metal chains, submerged valves, ship propellers, steel hooks, anchor parts.
                </p>
              </div>
            </div>
          </div>

          {/* Missing Canonical Targets */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-800 font-mono">
              <XCircle className="w-4 h-4 text-rose-600" />
              Untrained Canonical Production Classes
            </div>

            <div className="p-4 bg-slate-50 border border-border-subtle rounded-xl space-y-3 text-xs text-text-muted">
              <p className="text-xs text-text-secondary leading-relaxed">
                The canonical taxonomy contains 3 additional categories which have zero acoustic imagery in this benchmark. To maintain scientific integrity, the model makes no claims on these classes:
              </p>
              <div className="space-y-2 font-mono">
                <div className="flex justify-between py-1 border-b border-border-subtle">
                  <span>derelict_fishing_gear (ghost pots, gillnets)</span>
                  <span className="text-rose-700 font-bold">0 samples</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border-subtle">
                  <span>shipwreck (submerged wooden/steel hulls)</span>
                  <span className="text-rose-700 font-bold">0 samples</span>
                </div>
                <div className="flex justify-between py-1">
                  <span>pipe_or_cylinder (exposed subsea pipelines)</span>
                  <span className="text-rose-700 font-bold">0 samples</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetPage;

import React from "react";
import { FileUploader } from "../components/upload/FileUploader";
import { Info, ShieldAlert, Cpu } from "lucide-react";

export const UploadPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-accent tracking-wide uppercase mb-1">
          <Cpu className="w-3.5 h-3.5" />
          Ingestion & Pipeline Dispatcher
        </div>
        <h1 className="text-2xl font-bold text-text-primary">
          Upload Sonar Survey
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Provide raw acoustic side-scan sonar files for real-time anomaly detection, quality scoring, and georeferencing.
        </p>
      </div>

      <FileUploader />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto pt-4">
        <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
            <Info className="w-4 h-4" />
            MVP Supported Formats
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Standard eXtended Triton Format (<code className="text-text-primary">.xtf</code>) with embedded per-ping navigation metadata and calibrated acoustic side-scan strips (<code className="text-text-primary">.png</code>).
          </p>
        </div>

        <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-blue-400">
            <ShieldAlert className="w-4 h-4" />
            Quality & Motion Scoring
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            All files undergo automatic acoustic dropout checks and motion quality evaluation prior to deep learning inference to prevent false positives.
          </p>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;

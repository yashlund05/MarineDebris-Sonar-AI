import React from "react";
import { UploadCloud, FileType, Info } from "lucide-react";

export const UploadPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-border-subtle pb-4">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          Upload Sonar Survey
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Accepts XTF, JSF, PNG sonar strips, and TIFF files up to 2 GB with optional navigation CSV.
        </p>
      </div>

      <div className="border-2 border-dashed border-border-subtle rounded-xl p-12 text-center bg-bg-surface flex flex-col items-center justify-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-accent/10 border border-accent/30 flex items-center justify-center text-accent">
          <UploadCloud className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <p className="text-text-primary font-medium">Sonar Ingestion Shell (Phase 0)</p>
          <p className="text-xs text-text-secondary max-w-md">
            File ingestion, XTF streaming parsers, and processing job queues will be connected during Phase 1.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs text-text-muted font-mono">
          <FileType className="w-4 h-4" />
          <span>Supported Spec Formats: .xtf, .jsf, .png, .tif, .tiff</span>
        </div>
      </div>

      <div className="bg-bg-surface border border-border-subtle rounded-lg p-4 flex items-start space-x-3 text-xs text-text-secondary">
        <Info className="w-4 h-4 text-accent mt-0.5 shrink-0" />
        <p>
          According to PRD.md §4.1: XTF binary parsing and PNG strip loading are initial MVP formats. JSF and TIFF routing are reserved in the API/DB schema for forward compatibility.
        </p>
      </div>
    </div>
  );
};

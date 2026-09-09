import React from "react";
import { Waves } from "lucide-react";
import { SonarEnhancementWorkbench } from "../components/sonar/SonarEnhancementWorkbench";

export const SonarEnhancementPage: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-accent/10 rounded-xl">
            <Waves className="w-5 h-5 text-accent" />
          </div>
          <h1 className="text-xl font-bold text-text-primary tracking-tight">
            Sonar Image Enhancement & Visualization
          </h1>
        </div>
        <p className="text-xs text-text-secondary max-w-3xl">
          Domain-aware acoustic radiometric filtering adapting open-source{" "}
          <span className="font-mono font-medium text-text-primary">sonoware/sidescantools</span> (GPL-3.0).
          Provides 2D-FFT stripe suppression, CLAHE dynamic range equalization, non-reference quality diagnostics,
          and interactive raw vs enhanced split slider inspection.
        </p>
      </div>

      {/* Interactive Workbench */}
      <SonarEnhancementWorkbench />
    </div>
  );
};

export default SonarEnhancementPage;

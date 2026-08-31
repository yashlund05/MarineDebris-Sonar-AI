import React from "react";
import { Database } from "lucide-react";

export const SurveysPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-border-subtle pb-4">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          Survey Archive & Sessions
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Historical sonar surveys, processing runs, and detection audit logs.
        </p>
      </div>

      <div className="bg-bg-surface border border-border-subtle rounded-lg p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-bg-elevated flex items-center justify-center mx-auto text-text-secondary">
          <Database className="w-6 h-6" />
        </div>
        <h3 className="text-text-primary font-semibold">Survey Repository Ready</h3>
        <p className="text-xs text-text-secondary max-w-sm mx-auto">
          Database schema and tables initialized. Survey records and detection archives will populate when pipeline processing begins.
        </p>
      </div>
    </div>
  );
};

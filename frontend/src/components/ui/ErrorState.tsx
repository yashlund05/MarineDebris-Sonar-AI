import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Error Encountered",
  message = "Failed to communicate with the backend service.",
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-bg-surface border border-border-subtle rounded-lg max-w-md mx-auto my-6">
      <div className="w-12 h-12 rounded-full bg-detection-debris/10 flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6 text-detection-debris" />
      </div>
      <h3 className="text-text-primary font-semibold text-base mb-1">{title}</h3>
      <p className="text-text-secondary text-sm mb-5">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-accent hover:bg-accent-hover text-white transition-colors duration-150"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Connection
        </button>
      )}
    </div>
  );
};

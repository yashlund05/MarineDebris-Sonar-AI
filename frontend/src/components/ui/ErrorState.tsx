import React, { useState } from "react";
import { AlertCircle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { Link } from "react-router-dom";

interface ErrorStateProps {
  title?: string;
  message?: string;
  errorCode?: string;
  details?: string;
  onRetry?: () => void;
  actionLabel?: string;
  actionHref?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Service Interruption",
  message = "The requested acoustic sonar service could not complete the operation.",
  errorCode,
  details,
  onRetry,
  actionLabel,
  actionHref,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-bg-surface border border-rose-200 rounded-2xl max-w-md mx-auto my-8 shadow-card">
      <div className="w-12 h-12 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center mb-4 text-rose-600">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-text-primary font-semibold text-base mb-1">{title}</h3>
      <p className="text-text-secondary text-xs mb-3 leading-relaxed max-w-sm">{message}</p>

      {errorCode && (
        <span className="inline-block px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-md font-mono text-[11px] font-semibold mb-4">
          Error: {errorCode}
        </span>
      )}

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-xl bg-accent hover:bg-accent-hover text-white transition-all shadow-sm cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            Retry Connection
          </button>
        )}
        {actionLabel && actionHref && (
          <Link
            to={actionHref}
            className="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-xl border border-border-default hover:bg-bg-elevated text-text-primary transition-all"
          >
            {actionLabel}
          </Link>
        )}
      </div>

      {details && (
        <div className="w-full mt-5 text-left border-t border-border-subtle pt-3">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-[11px] text-text-muted hover:text-text-secondary flex items-center justify-between w-full font-medium cursor-pointer"
          >
            <span>Technical Details</span>
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {showDetails && (
            <pre className="mt-2 p-3 bg-slate-900 text-slate-100 rounded-lg text-[10px] font-mono overflow-x-auto whitespace-pre-wrap">
              {details}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

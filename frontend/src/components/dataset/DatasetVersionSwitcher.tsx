import React from "react";
import { useSearchParams } from "react-router-dom";
import { DatasetVersion } from "../../types/dataset";
import { clsx } from "clsx";

interface Props {
  versions?: DatasetVersion[];
  isLoading: boolean;
}

export const DatasetVersionSwitcher: React.FC<Props> = ({ versions, isLoading }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentVersion = searchParams.get("version") || "v3";

  if (isLoading) {
    return <div className="h-10 w-full animate-pulse bg-bg-elevated rounded-xl"></div>;
  }

  if (!versions || versions.length === 0) {
    return null;
  }

  const displayVersions = versions;

  return (
    <div className="flex flex-wrap items-center gap-2 mb-6">
      <span className="text-sm font-semibold text-text-secondary mr-2">Dataset Version:</span>
      <div className="flex flex-wrap gap-2 p-1 bg-bg-elevated border border-border-subtle rounded-xl">
        {displayVersions.map((v) => {
          const isActive = v.version_id === currentVersion;
          return (
            <button
              key={v.version_id}
              onClick={() => {
                setSearchParams({ version: v.version_id });
              }}
              className={clsx(
                "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all flex flex-col items-center cursor-pointer",
                isActive
                  ? "bg-bg-surface text-accent shadow-sm border border-border-default"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-subtle border border-transparent"
              )}
            >
              <span className="uppercase">{v.name || v.version_id}</span>
              <span
                className={clsx(
                  "text-[9px] mt-0.5 px-1.5 rounded-full border",
                  v.status === "FROZEN_READY"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : v.status === "LEGACY"
                    ? "bg-slate-100 text-slate-600 border-slate-200"
                    : "bg-amber-50 text-amber-700 border-amber-200"
                )}
              >
                {v.status}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

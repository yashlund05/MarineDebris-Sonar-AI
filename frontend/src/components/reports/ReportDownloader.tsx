import React, { useState } from "react";
import { Download, FileJson, FileSpreadsheet, Map, Loader2 } from "lucide-react";
import { reportsApi } from "../../api/reports";
import { ReportFormat } from "../../types";

interface ReportDownloaderProps {
  surveyId: string;
}

export const ReportDownloader: React.FC<ReportDownloaderProps> = ({ surveyId }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [loadingFormat, setLoadingFormat] = useState<ReportFormat | null>(null);

  const handleDownload = async (format: ReportFormat) => {
    setLoadingFormat(format);
    try {
      const response = await reportsApi.generateReport(surveyId, { format });
      if (response.success && response.data) {
        // Trigger download
        const url = reportsApi.getDownloadUrl(response.data.report_id);
        window.open(url, "_blank");
      }
    } catch (e) {
      console.error("Failed to generate report:", e);
    } finally {
      setLoadingFormat(null);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3.5 py-2 bg-bg-surface hover:bg-bg-elevated border border-border-subtle text-text-primary text-xs font-semibold rounded-xl transition-all shadow-sm cursor-pointer"
      >
        <Download className="w-4 h-4 text-accent" />
        Export Audit Report
      </button>

      {isOpen && (
        <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-xl shadow-2xl bg-bg-surface border border-border-subtle divide-y divide-border-subtle z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="p-2 space-y-1">
            <button
              onClick={() => handleDownload("json")}
              disabled={loadingFormat !== null}
              className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-bg-elevated flex items-center justify-between text-text-primary transition-all disabled:opacity-50 cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <FileJson className="w-4 h-4 text-amber-400" />
                <div>
                  <p className="font-medium">JSON Audit Report</p>
                  <p className="text-[10px] text-text-muted">Full telemetry & metadata</p>
                </div>
              </div>
              {loadingFormat === "json" && <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />}
            </button>

            <button
              onClick={() => handleDownload("csv")}
              disabled={loadingFormat !== null}
              className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-bg-elevated flex items-center justify-between text-text-primary transition-all disabled:opacity-50 cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <div>
                  <p className="font-medium">CSV Spreadsheet</p>
                  <p className="text-[10px] text-text-muted">Tabular detection list</p>
                </div>
              </div>
              {loadingFormat === "csv" && <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />}
            </button>

            <button
              onClick={() => handleDownload("geojson")}
              disabled={loadingFormat !== null}
              className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-bg-elevated flex items-center justify-between text-text-primary transition-all disabled:opacity-50 cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <Map className="w-4 h-4 text-cyan-400" />
                <div>
                  <p className="font-medium">GeoJSON FeatureCollection</p>
                  <p className="text-[10px] text-text-muted">GIS spatial layers</p>
                </div>
              </div>
              {loadingFormat === "geojson" && <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

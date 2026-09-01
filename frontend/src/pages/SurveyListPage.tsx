import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { surveysApi } from "../api/surveys";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import {
  Database,
  ArrowRight,
  Trash2,
  HardDrive,
  Calendar,
  Layers,
  UploadCloud,
} from "lucide-react";
import { Survey } from "../types";

export const SurveyListPage: React.FC = () => {
  const queryClient = useQueryClient();

  const {
    data: surveysResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["surveys"],
    queryFn: () => surveysApi.getSurveys({ limit: 50 }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => surveysApi.deleteSurvey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["surveys"] });
    },
  });

  if (isLoading) {
    return <LoadingState message="Fetching survey catalog from database..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to Load Surveys"
        message="Unable to communicate with the survey archive service."
      />
    );
  }

  const surveys = surveysResponse?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Database className="w-6 h-6 text-accent" />
            Survey Archive
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Historical acoustic sessions, automated anomaly results, and telemetry records.
          </p>
        </div>

        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition-all shadow-md"
        >
          <UploadCloud className="w-4 h-4" />
          Upload New Record
        </Link>
      </div>

      {surveys.length === 0 ? (
        <div className="bg-bg-surface border border-border-subtle rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 shadow-lg">
          <div className="p-4 bg-bg-elevated rounded-full w-16 h-16 mx-auto flex items-center justify-center text-text-muted">
            <Database className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-text-primary">No Surveys Stored</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              No side-scan sonar files have been uploaded to the system yet.
            </p>
          </div>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition-all shadow-md"
          >
            Upload First Survey
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {surveys.map((survey: Survey) => {
            const statusColors: Record<string, string> = {
              complete: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
              failed: "text-red-400 bg-red-500/10 border-red-500/30",
              uploaded: "text-blue-400 bg-blue-500/10 border-blue-500/30",
              queued: "text-amber-400 bg-amber-500/10 border-amber-500/30",
              preprocessing: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
              inferring: "text-purple-400 bg-purple-500/10 border-purple-500/30",
            };

            const statusClass =
              statusColors[survey.status] || "text-text-secondary bg-bg-elevated border-border-subtle";

            return (
              <div
                key={survey.id}
                className="p-5 bg-bg-surface border border-border-subtle rounded-2xl space-y-4 hover:border-accent/40 transition-all flex flex-col justify-between shadow-md"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border capitalize ${statusClass}`}
                    >
                      {survey.status}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        if (confirm(`Delete survey record ${survey.source_filename}?`)) {
                          deleteMutation.mutate(survey.id);
                        }
                      }}
                      className="text-text-muted hover:text-red-400 p-1 rounded transition-colors cursor-pointer"
                      title="Delete survey"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div>
                    <h3 className="font-semibold text-sm text-text-primary truncate" title={survey.source_filename}>
                      {survey.source_filename}
                    </h3>
                    <p className="font-mono text-[11px] text-text-muted mt-0.5 truncate">
                      ID: {survey.id}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono text-text-secondary pt-2 border-t border-border-subtle/50">
                    <span className="flex items-center gap-1.5">
                      <HardDrive className="w-3.5 h-3.5 text-text-muted" />
                      {(survey.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </span>
                    <span className="flex items-center gap-1.5 justify-end uppercase font-semibold text-accent">
                      <Layers className="w-3.5 h-3.5" />
                      {survey.file_type}
                    </span>
                    <span className="flex items-center gap-1.5 col-span-2 text-text-muted">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(survey.created_at).toLocaleDateString()} at{" "}
                      {new Date(survey.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-border-subtle flex items-center justify-between">
                  <span className="text-xs font-mono text-text-secondary">
                    <strong className="text-text-primary font-bold">
                      {(survey as any).detection_count ?? 0}
                    </strong>{" "}
                    detections
                  </span>

                  <Link
                    to={`/surveys/${survey.id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-accent/10 hover:bg-accent text-accent hover:text-white rounded-lg text-xs font-semibold transition-all"
                  >
                    Inspect
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SurveyListPage;

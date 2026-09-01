import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { surveysApi } from "../api/surveys";
import { detectionsApi } from "../api/detections";
import { SonarViewer } from "../components/sonar/SonarViewer";
import { DetectionPanel } from "../components/detections/DetectionPanel";
import { DetectionMap } from "../components/map/DetectionMap";
import { DetectionDetail } from "../components/detections/DetectionDetail";
import { JobStatusBar } from "../components/jobs/JobStatusBar";
import { FilterBar } from "../components/ui/FilterBar";
import { ReportDownloader } from "../components/reports/ReportDownloader";
import { ErrorState } from "../components/ui/ErrorState";
import {
  ArrowLeft,
  Waves,
  Map,
  Eye,
  Calendar,
  HardDrive,
  Radio,
} from "lucide-react";

export const SurveyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeView, setActiveView] = useState<"viewer" | "map" | "split">("viewer");

  // Fetch survey metadata
  const {
    data: surveyData,
    isLoading: isSurveyLoading,
    error: surveyError,
  } = useQuery({
    queryKey: ["survey", id],
    queryFn: () => surveysApi.getSurvey(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      return status === "complete" || status === "failed" ? false : 3000;
    },
  });

  // Fetch detections
  const { data: detectionsData } = useQuery({
    queryKey: ["detections", id],
    queryFn: () => detectionsApi.getSurveyDetections(id!, { limit: 500, include_filtered: true }),
    enabled: !!id,
  });

  if (isSurveyLoading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="h-6 w-32 bg-slate-200 animate-pulse rounded" />
        </div>
        <div className="h-[600px] bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card flex items-center justify-center">
          <div className="text-center space-y-2">
            <Waves className="w-8 h-8 text-accent animate-pulse mx-auto" />
            <p className="text-xs text-text-muted font-mono">Streaming acoustic sonar session...</p>
          </div>
        </div>
      </div>
    );
  }

  if (surveyError || !surveyData?.data) {
    return (
      <ErrorState
        title="Acoustic Survey Not Found"
        message="The requested sonar survey session could not be retrieved from the catalog."
        actionLabel="Return to Surveys"
        actionHref="/surveys"
      />
    );
  }

  const survey = surveyData.data;
  const detections = detectionsData?.data || [];
  const latestJob = (survey as any).latest_job;

  return (
    <div className="space-y-4 flex flex-col h-[calc(100vh-6rem)]">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 flex-shrink-0 bg-bg-surface p-4 rounded-2xl border border-border-subtle shadow-card">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              to="/surveys"
              className="p-1 text-text-muted hover:text-text-primary rounded-lg hover:bg-slate-100 transition-all"
              title="Back to Surveys"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Waves className="w-4 h-4 text-accent" />
              {survey.source_filename}
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              #{survey.id.slice(0, 8)}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-text-muted">
            <span className="flex items-center gap-1">
              <HardDrive className="w-3 h-3" />
              {(survey.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
            </span>
            <span>•</span>
            <span className="uppercase font-bold text-accent">{survey.file_type}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Radio className="w-3 h-3" />
              Swath: {survey.channel || "starboard"}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(survey.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        {/* View Mode Switcher and Actions */}
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-100 border border-border-subtle p-0.5 rounded-xl text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveView("viewer")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg transition-all text-xs ${
                activeView === "viewer"
                  ? "bg-bg-surface text-text-primary font-bold shadow-xs"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              Acoustic Strip
            </button>
            <button
              type="button"
              onClick={() => setActiveView("split")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg transition-all text-xs ${
                activeView === "split"
                  ? "bg-bg-surface text-text-primary font-bold shadow-xs"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              Split View
            </button>
            <button
              type="button"
              onClick={() => setActiveView("map")}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg transition-all text-xs ${
                activeView === "map"
                  ? "bg-bg-surface text-text-primary font-bold shadow-xs"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Map className="w-3.5 h-3.5" />
              GIS Map
            </button>
          </div>

          <ReportDownloader surveyId={survey.id} />
        </div>
      </div>

      {/* Live Celery Processing Job Bar */}
      {latestJob && (
        <div className="flex-shrink-0">
          <JobStatusBar
            jobId={latestJob.id}
            initialStatus={latestJob.status}
            initialProgress={latestJob.progress_pct}
            initialStage={latestJob.current_stage}
          />
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex-shrink-0">
        <FilterBar />
      </div>

      {/* Main Content Workspace (Sonar Viewer + Detections Panel) */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Sonar Imaging Workstation */}
        <div className="lg:col-span-8 flex flex-col min-h-0">
          {activeView === "viewer" && (
            <div className="flex-1 min-h-0">
              <SonarViewer surveyId={survey.id} detections={detections} />
            </div>
          )}

          {activeView === "map" && (
            <div className="flex-1 min-h-0">
              <DetectionMap detections={detections} />
            </div>
          )}

          {activeView === "split" && (
            <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 gap-4">
              <SonarViewer surveyId={survey.id} detections={detections} />
              <DetectionMap detections={detections} />
            </div>
          )}
        </div>

        {/* Right Inspection Panel: Detections Summary */}
        <div className="lg:col-span-4 flex flex-col min-h-0">
          <DetectionPanel detections={detections} />
        </div>
      </div>

      {/* Details Modal */}
      <DetectionDetail />
    </div>
  );
};

export default SurveyDetailPage;

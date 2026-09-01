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
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { ArrowLeft, Waves, Map, Eye, Calendar, HardDrive, Radio } from "lucide-react";

export const SurveyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeView, setActiveView] = useState<"viewer" | "map" | "split">("split");

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
      // Poll faster if job is not yet complete
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
    return <LoadingState message="Loading acoustic survey session..." />;
  }

  if (surveyError || !surveyData?.data) {
    return (
      <ErrorState
        title="Survey Not Found"
        message="The requested sonar survey session could not be retrieved."
      />
    );
  }

  const survey = surveyData.data;
  const detections = detectionsData?.data || [];
  const latestJob = (survey as any).latest_job;

  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-5rem)]">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              to="/surveys"
              className="p-1 text-text-secondary hover:text-text-primary rounded-lg hover:bg-bg-surface transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-xl font-bold text-text-primary flex items-center gap-2.5">
              <Waves className="w-5 h-5 text-accent" />
              {survey.source_filename}
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-text-secondary">
            <span className="flex items-center gap-1">
              <HardDrive className="w-3.5 h-3.5 text-text-muted" />
              {(survey.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
            </span>
            <span>•</span>
            <span className="uppercase font-semibold text-accent">{survey.file_type}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Radio className="w-3.5 h-3.5 text-text-muted" />
              Swath: {survey.channel || "starboard"}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-text-muted" />
              {new Date(survey.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        {/* View Mode Switcher and Export */}
        <div className="flex items-center gap-3">
          <div className="flex bg-bg-surface border border-border-subtle p-1 rounded-xl text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveView("viewer")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeView === "viewer"
                  ? "bg-accent text-white font-semibold shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              Acoustic Strip
            </button>
            <button
              type="button"
              onClick={() => setActiveView("split")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeView === "split"
                  ? "bg-accent text-white font-semibold shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              Split View
            </button>
            <button
              type="button"
              onClick={() => setActiveView("map")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeView === "map"
                  ? "bg-accent text-white font-semibold shadow-sm"
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

      {/* Main Content Workspace (Viewer + Panel + Map) */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Visualizers Area (Sonar Viewer / Map) */}
        <div className="lg:col-span-8 flex flex-col min-h-0 gap-4">
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

        {/* Right Sidebar: Detections Panel */}
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

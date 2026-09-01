import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { surveysApi } from "../api/surveys";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import {
  Database,
  Trash2,
  UploadCloud,
  Search,
  Filter,
  Eye,
  ArrowUpDown,
} from "lucide-react";
import { Survey } from "../types";

export const SurveyListPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<"created_at" | "source_filename">("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const {
    data: surveysResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["surveys"],
    queryFn: () => surveysApi.getSurveys({ limit: 100 }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => surveysApi.deleteSurvey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["surveys"] });
    },
  });

  const surveys: Survey[] = surveysResponse?.data || [];

  const filteredSurveys = useMemo(() => {
    return surveys
      .filter((s) => {
        if (statusFilter !== "all" && s.status !== statusFilter) return false;
        if (
          searchTerm &&
          !s.source_filename.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !s.id.toLowerCase().includes(searchTerm.toLowerCase())
        ) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortField === "created_at") {
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          return sortOrder === "asc" ? dateA - dateB : dateB - dateA;
        }
        return sortOrder === "asc"
          ? a.source_filename.localeCompare(b.source_filename)
          : b.source_filename.localeCompare(a.source_filename);
      });
  }, [surveys, searchTerm, statusFilter, sortField, sortOrder]);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Surveys Archive</h1>
          <p className="text-xs text-text-secondary">Loading acoustic catalog...</p>
        </div>
        <div className="bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
          <TableSkeleton rows={6} cols={6} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to Load Surveys Archive"
        message="Unable to communicate with the survey catalog service."
        onRetry={() => queryClient.invalidateQueries({ queryKey: ["surveys"] })}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Database className="w-6 h-6 text-accent" />
            Surveys Archive
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Historical acoustic sessions, automated anomaly results, and telemetry records.
          </p>
        </div>

        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition-all shadow-sm"
        >
          <UploadCloud className="w-4 h-4" />
          Ingest New Survey
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-4 shadow-card flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[240px] max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by survey filename or ID..."
              className="w-full pl-9 pr-3 py-1.5 bg-bg-elevated border border-border-subtle rounded-xl text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <Filter className="w-3.5 h-3.5" />
            <span>Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-bg-elevated border border-border-subtle rounded-lg px-2.5 py-1 text-xs text-text-primary font-medium focus:outline-none"
          >
            <option value="all">All Statuses ({surveys.length})</option>
            <option value="complete">Complete</option>
            <option value="queued">Queued / Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Main Surveys Data Table */}
      {filteredSurveys.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No Sonar Surveys Found"
          description="Upload your first Forward-Looking Sonar or sidescan sonar file to begin acoustic analysis."
          actionLabel="Ingest New Survey"
          actionHref="/upload"
        />
      ) : (
        <div className="bg-bg-surface border border-border-subtle rounded-2xl shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-bg-elevated text-text-secondary uppercase tracking-wider font-mono text-[11px]">
                <tr>
                  <th className="py-3 px-4 font-semibold">Survey Filename</th>
                  <th className="py-3 px-4 font-semibold">Format</th>
                  <th className="py-3 px-4 font-semibold">File Size</th>
                  <th className="py-3 px-4 font-semibold">Detections</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th
                    className="py-3 px-4 font-semibold cursor-pointer hover:text-text-primary"
                    onClick={() => {
                      if (sortField === "created_at") {
                        setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                      } else {
                        setSortField("created_at");
                        setSortOrder("desc");
                      }
                    }}
                  >
                    <span className="flex items-center gap-1">
                      Uploaded <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th className="py-3 px-4 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {filteredSurveys.map((survey) => {
                  const detectionCount = (survey as any).detection_count || 0;
                  return (
                    <tr
                      key={survey.id}
                      onClick={() => navigate(`/surveys/${survey.id}`)}
                      className="hover:bg-bg-elevated/40 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-bold text-text-primary">
                        <div className="flex items-center gap-2">
                          <span className="truncate max-w-xs">{survey.source_filename}</span>
                          <span className="text-[10px] text-text-muted font-mono font-normal">
                            #{survey.id.slice(0, 8)}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono uppercase text-accent font-semibold">
                        {survey.file_type}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-text-secondary">
                        {(survey.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-text-primary">
                        {detectionCount}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                            survey.status === "complete"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : survey.status === "failed"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-sky-50 text-sky-700 border border-sky-200"
                          }`}
                        >
                          {survey.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-text-muted text-[11px]">
                        {new Date(survey.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div
                          className="flex items-center justify-end gap-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Link
                            to={`/surveys/${survey.id}`}
                            className="p-1.5 text-text-secondary hover:text-accent rounded-lg hover:bg-bg-elevated transition-all"
                            title="Inspect Survey"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button
                            type="button"
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Delete survey session "${survey.source_filename}" and all associated detections?`
                                )
                              ) {
                                deleteMutation.mutate(survey.id);
                              }
                            }}
                            className="p-1.5 text-text-muted hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-all cursor-pointer"
                            title="Delete Survey"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveyListPage;

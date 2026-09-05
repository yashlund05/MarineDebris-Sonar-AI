import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Cpu, RefreshCw } from "lucide-react";
import { modelsApi } from "../api/models";
import { ModelOverviewCard } from "../components/model/ModelOverviewCard";
import { ExperimentSelector } from "../components/model/ExperimentSelector";
import { MetricSummary } from "../components/model/MetricSummary";
import { MultiSeedStability } from "../components/model/MultiSeedStability";
import { PromotionGateCard } from "../components/model/PromotionGateCard";
import { LatencyAndFalseAlarm } from "../components/model/LatencyAndFalseAlarm";
import { ExplainabilityAndArtifacts } from "../components/model/ExplainabilityAndArtifacts";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";

export const ModelEvaluationPage: React.FC = () => {
  const [selectedModelId, setSelectedModelId] = useState<string>("production_fls_yolov8n");

  const {
    data: modelsData,
    isLoading: isLoadingModels,
    error: modelsError,
    refetch: refetchModels,
  } = useQuery({
    queryKey: ["models-list"],
    queryFn: () => modelsApi.getModels(),
  });

  const models = modelsData?.data || [];
  const selectedModel = models.find((m) => m.id === selectedModelId) || models[0];

  const effectiveModelId = selectedModel?.id || selectedModelId;

  const {
    data: metricsData,
  } = useQuery({
    queryKey: ["model-metrics", effectiveModelId],
    queryFn: () => modelsApi.getModelMetrics(effectiveModelId),
    enabled: !!effectiveModelId,
  });

  const {
    data: runsData,
  } = useQuery({
    queryKey: ["model-runs", effectiveModelId],
    queryFn: () => modelsApi.getModelRuns(effectiveModelId),
    enabled: !!effectiveModelId,
  });

  const {
    data: promotionData,
  } = useQuery({
    queryKey: ["model-promotion", effectiveModelId],
    queryFn: () => modelsApi.getModelPromotion(effectiveModelId),
    enabled: !!effectiveModelId,
  });

  const {
    data: artifactsData,
  } = useQuery({
    queryKey: ["model-artifacts", effectiveModelId],
    queryFn: () => modelsApi.getModelArtifacts(effectiveModelId),
    enabled: !!effectiveModelId,
  });

  const {
    data: explanationsData,
  } = useQuery({
    queryKey: ["model-explanations", effectiveModelId],
    queryFn: () => modelsApi.getModelExplanations(effectiveModelId),
    enabled: !!effectiveModelId,
  });

  if (isLoadingModels) {
    return <LoadingState message="Loading Model Registry and Research Evaluation artifacts..." />;
  }

  if (modelsError || !selectedModel) {
    return (
      <ErrorState
        title="Model Intelligence Service Offline"
        message="Unable to load model metadata from backend API. Please check server status."
        onRetry={refetchModels}
      />
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider font-mono mb-1">
            <Cpu className="w-3.5 h-3.5" />
            Acoustic Machine Learning Intelligence
          </div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">
            Model Evaluation & Performance Intelligence
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Empirically verified detection metrics, multi-seed variance, false-alarm profiles, and promotion gate audits.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetchModels()}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-bg-surface border border-border-subtle rounded-xl text-xs font-mono text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Evaluation
          </button>
        </div>
      </div>

      {/* Model & Checkpoint Selection */}
      <ExperimentSelector
        models={models}
        selectedModelId={effectiveModelId}
        onSelectModel={setSelectedModelId}
      />

      {/* Primary Model Overview Card */}
      <ModelOverviewCard model={selectedModel} />

      {/* Metric Summary Panel */}
      {metricsData?.data && (
        <MetricSummary metricsResponse={metricsData.data} />
      )}

      {/* Promotion Gate Audit */}
      {promotionData?.data && (
        <PromotionGateCard promotion={promotionData.data} />
      )}

      {/* Latency and False Alarm Analysis */}
      {metricsData?.data && (
        <LatencyAndFalseAlarm metricsResponse={metricsData.data} />
      )}

      {/* Multi-Seed Robustness Section */}
      {runsData?.data && (
        <MultiSeedStability runsResponse={runsData.data} />
      )}

      {/* Explainability & Artifacts */}
      <ExplainabilityAndArtifacts
        explanation={explanationsData?.data}
        artifactsResponse={artifactsData?.data}
      />
    </div>
  );
};

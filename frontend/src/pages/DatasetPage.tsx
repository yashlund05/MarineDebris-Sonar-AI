import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { datasetApi } from "../api/datasets";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";

import { DatasetVersionSwitcher } from "../components/dataset/DatasetVersionSwitcher";
import { DatasetOverview } from "../components/dataset/DatasetOverview";
import { DatasetEvolution } from "../components/dataset/DatasetEvolution";
import { DatasetScope } from "../components/dataset/DatasetScope";
import { SensorProfileComponent } from "../components/dataset/SensorProfile";
import { SourceAccountingTable } from "../components/dataset/SourceAccountingTable";
import { SplitDistribution } from "../components/dataset/SplitDistribution";
import { IntegrityAudit } from "../components/dataset/IntegrityAudit";
import { ClassDistributionComponent } from "../components/dataset/ClassDistribution";
import { TaxonomyPanel } from "../components/dataset/TaxonomyPanel";
import { ScaleDistributionComponent } from "../components/dataset/ScaleDistribution";
import { HardNegativePanel } from "../components/dataset/HardNegativePanel";
import { BenchmarkSummary } from "../components/dataset/BenchmarkSummary";
import { ProvenanceCard } from "../components/dataset/ProvenanceCard";
import { DatasetLimitations } from "../components/dataset/DatasetLimitations";

export const DatasetPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const version = searchParams.get("version") || "v3";

  const { data: versionsData, isLoading: isLoadingVersions } = useQuery({
    queryKey: ["dataset-versions"],
    queryFn: datasetApi.getVersions,
  });

  const { data: summaryData, isLoading: isLoadingSummary, isError, error, refetch } = useQuery({
    queryKey: ["dataset-summary", version],
    queryFn: () => datasetApi.getSummary(version),
    retry: 1,
  });

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Dataset Explorer</h1>
        <p className="text-text-secondary">
          Scientific accounting, lineage, and benchmark performance for the MarineDebris-Sonar-AI canonical datasets.
        </p>
      </div>

      <DatasetVersionSwitcher versions={versionsData} isLoading={isLoadingVersions} />

      {isLoadingSummary && (
        <LoadingState message="Loading dataset metadata and scientific accounting..." />
      )}

      {isError && (
        <ErrorState
          title="DATASET METADATA UNAVAILABLE"
          message={`Could not load dataset accounting for version ${version.toUpperCase()}. No fallback data is available.`}
          errorCode={error instanceof Error ? error.message : "API_ERROR"}
          onRetry={refetch}
        />
      )}

      {summaryData && !isLoadingSummary && !isError && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <DatasetOverview overview={summaryData.overview} />
          <DatasetEvolution lineage={summaryData.lineage} />
          <DatasetScope sensor={summaryData.sensor} limitations={summaryData.limitations} />
          <SensorProfileComponent sensor={summaryData.sensor} />
          <SourceAccountingTable source_level_accounting={summaryData.source_level_accounting} />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <SplitDistribution splits={summaryData.splits} />
            <IntegrityAudit integrity={summaryData.integrity} />
          </div>
          
          <ClassDistributionComponent distribution={summaryData.class_distribution} taxonomy={summaryData.taxonomy} />
          <TaxonomyPanel taxonomy={summaryData.taxonomy} />
          <ScaleDistributionComponent scale_distribution={summaryData.scale_distribution} />
          <HardNegativePanel hard_negatives={summaryData.hard_negatives} />
          <BenchmarkSummary benchmarks={summaryData.benchmarks} />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <ProvenanceCard provenance={summaryData.provenance} />
            <DatasetLimitations limitations={summaryData.limitations} />
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetPage;

import React from "react";
import { SensorProfile, LimitationData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Microscope, AlertTriangle } from "lucide-react";

interface Props {
  sensor: Confident<SensorProfile>;
  limitations: Confident<LimitationData>;
}

export const DatasetScope: React.FC<Props> = ({ sensor, limitations }) => {
  const { data: sensorData, confidence: sensorConf } = sensor;
  const { data: limData } = limitations;

  const getConf = () => sensorConf; // using sensor conf for the header

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <Microscope className="w-5 h-5 mr-2 text-accent" />
          Scientific Scope
        </h2>
        <ConfidenceStateBadge state={getConf()} />
      </div>

      {!sensorData ? (
        <div className="text-sm text-text-secondary">Not Available</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ScopeItem label="Modality" value={sensorData.modality} />
          <ScopeItem label="Sensor" value={sensorData.sonar_camera} />
          <ScopeItem label="Frequency" value={sensorData.frequency} />
          <ScopeItem label="Primary Environment" value={sensorData.primary_environment} />
          <ScopeItem label="Additional Negative Domain" value={sensorData.additional_negative_domain} />
          <ScopeItem label="Core Data Type" value={sensorData.core_data_type} />
          <ScopeItem label="Synthetic Auxiliary" value={sensorData.synthetic_auxiliary} />
          <ScopeItem label="Canonical Taxonomy Coverage" value={sensorData.canonical_taxonomy_coverage} />
        </div>
      )}

      {limData?.generalization_note && (
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex gap-3 text-amber-900 text-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <div>
            <span className="font-semibold block mb-1">Generalization Notice:</span>
            {limData.generalization_note}
          </div>
        </div>
      )}
    </div>
  );
};

const ScopeItem = ({ label, value }: { label: string; value?: string }) => (
  <div className="p-3 bg-bg-elevated border border-border-subtle rounded-lg">
    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">{label}</div>
    <div className="text-sm font-medium text-text-primary">{value || "N/A"}</div>
  </div>
);

import React from "react";
import { SensorProfile, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Radio } from "lucide-react";

interface Props {
  sensor: Confident<SensorProfile>;
}

export const SensorProfileComponent: React.FC<Props> = ({ sensor }) => {
  const { data, confidence } = sensor;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Radio className="w-5 h-5 mr-2 text-accent" />
            Sensor Profile
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const items = [
    { label: "Sonar System", value: data.sonar_camera },
    { label: "Frequency Range", value: data.frequency },
    { label: "Institution", value: data.institution },
    { label: "Principal Investigator", value: data.pi },
    { label: "DOI", value: data.doi },
    { label: "License", value: data.license },
  ];

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <Radio className="w-5 h-5 mr-2 text-accent" />
          Sensor Profile
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((item, idx) => (
          <div key={idx} className="flex flex-col">
            <span className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
              {item.label}
            </span>
            <span className="text-sm text-text-primary font-medium">
              {item.value || "Not Available"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

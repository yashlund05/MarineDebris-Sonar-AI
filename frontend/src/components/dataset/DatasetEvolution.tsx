import React from "react";
import { LineageData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { GitMerge, ArrowRight } from "lucide-react";

interface Props {
  lineage: Confident<LineageData>;
}

export const DatasetEvolution: React.FC<Props> = ({ lineage }) => {
  const { data, confidence } = lineage;

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <GitMerge className="w-5 h-5 mr-2 text-accent" />
            Dataset Evolution
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <GitMerge className="w-5 h-5 mr-2 text-accent" />
          Data Lineage & Construction
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="relative py-8 overflow-x-auto">
        <div className="flex items-center space-x-4 min-w-max px-4">
          {data.nodes.map((node, index) => {
            const isLast = index === data.nodes.length - 1;
            const edge = data.edges.find((e) => e.from === node.id);

            return (
              <React.Fragment key={node.id}>
                <div className="flex flex-col items-center bg-bg-elevated border border-border-default rounded-xl p-4 w-48 text-center shadow-sm">
                  <div className="font-bold text-sm text-text-primary mb-2">{node.label}</div>
                  {node.count_images !== undefined && (
                    <div className="text-xs text-text-secondary font-mono">
                      {node.count_images.toLocaleString()} imgs
                    </div>
                  )}
                  {node.count_annotations !== undefined && (
                    <div className="text-xs text-text-secondary font-mono">
                      {node.count_annotations.toLocaleString()} annots
                    </div>
                  )}
                </div>

                {!isLast && edge && (
                  <div className="flex flex-col items-center justify-center space-y-1 w-32 relative">
                    <span className="text-[10px] font-semibold text-text-muted text-center leading-tight absolute -top-6 w-40">
                      {edge.label}
                    </span>
                    <div className="flex items-center w-full">
                      <div className="h-0.5 bg-border-strong w-full"></div>
                      <ArrowRight className="w-4 h-4 text-border-strong -ml-2" />
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};

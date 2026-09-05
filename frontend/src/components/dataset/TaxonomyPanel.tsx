import React from "react";
import { TaxonomyData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { FileText, GitPullRequest } from "lucide-react";

interface Props {
  taxonomy: Confident<TaxonomyData>;
}

export const TaxonomyPanel: React.FC<Props> = ({ taxonomy }) => {
  const { data, confidence } = taxonomy;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <FileText className="w-5 h-5 mr-2 text-accent" />
            Taxonomy & Ontology
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <FileText className="w-5 h-5 mr-2 text-accent" />
          Canonical Taxonomy
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-secondary flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          Canonical Classes
        </h3>
        <div className="overflow-x-auto border border-border-subtle rounded-lg">
          <table className="w-full text-sm text-left">
            <thead className="bg-bg-elevated text-text-secondary text-xs uppercase font-semibold">
              <tr>
                <th className="px-4 py-3">Class ID</th>
                <th className="px-4 py-3">Class Name</th>
                <th className="px-4 py-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle bg-bg-surface">
              {data.canonical_classes?.map((cls, idx) => (
                <tr key={idx} className="hover:bg-bg-subtle">
                  <td className="px-4 py-3 font-mono text-xs">{cls.id}</td>
                  <td className="px-4 py-3 font-medium text-text-primary">{cls.name}</td>
                  <td className="px-4 py-3 text-text-secondary">{cls.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.source_mapping && data.source_mapping.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 text-text-secondary flex items-center">
            <GitPullRequest className="w-4 h-4 mr-2" />
            Source Class Mapping
          </h3>
          <div className="overflow-x-auto border border-border-subtle rounded-lg">
            <table className="w-full text-sm text-left">
              <thead className="bg-bg-elevated text-text-secondary text-xs uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">Source Class</th>
                  <th className="px-4 py-3">Mapped Canonical Class</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle bg-bg-surface">
                {data.source_mapping.map((map, idx) => (
                  <tr key={idx} className="hover:bg-bg-subtle">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">{map.source_class}</td>
                    <td className="px-4 py-3 font-medium text-text-primary">{map.mapped_canonical}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

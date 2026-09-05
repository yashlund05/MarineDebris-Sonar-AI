import React from "react";
import { ProvenanceData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { BookOpen } from "lucide-react";

interface Props {
  provenance: Confident<ProvenanceData[]>;
}

export const ProvenanceCard: React.FC<Props> = ({ provenance }) => {
  const { data, confidence } = provenance;

  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <BookOpen className="w-5 h-5 mr-2 text-accent" />
            Provenance & Attribution
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
          <BookOpen className="w-5 h-5 mr-2 text-accent" />
          Provenance & Attribution
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {data.map((prov, idx) => (
          <div key={idx} className="p-4 bg-bg-elevated border border-border-subtle rounded-xl flex flex-col">
            <h3 className="font-semibold text-text-primary mb-3 text-sm">{prov.source_name}</h3>
            
            <div className="space-y-3 flex-1">
              {prov.institutions && prov.institutions.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">Institutions</div>
                  <ul className="text-xs text-text-secondary list-disc pl-4 space-y-0.5">
                    {prov.institutions.map((inst, i) => <li key={i}>{inst}</li>)}
                  </ul>
                </div>
              )}
              
              {prov.publications && prov.publications.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">Publications</div>
                  <ul className="text-xs text-text-secondary list-disc pl-4 space-y-0.5">
                    {prov.publications.map((pub, i) => <li key={i}>{pub}</li>)}
                  </ul>
                </div>
              )}

              <div className="flex gap-4 pt-2 mt-auto border-t border-border-subtle">
                {prov.dois && prov.dois.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider">DOIs</div>
                    <div className="text-xs font-mono text-accent">{prov.dois.join(", ")}</div>
                  </div>
                )}
                {prov.licenses && prov.licenses.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Licenses</div>
                    <div className="text-xs font-medium text-text-secondary">{prov.licenses.join(", ")}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

import React from "react";
import { SourceAccounting, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Table as TableIcon } from "lucide-react";

interface Props {
  source_level_accounting: Confident<SourceAccounting[]>;
}

export const SourceAccountingTable: React.FC<Props> = ({ source_level_accounting }) => {
  const { data, confidence } = source_level_accounting;

  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <TableIcon className="w-5 h-5 mr-2 text-accent" />
            Source Level Accounting
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  // Calculate totals
  const totals = data.reduce(
    (acc, curr) => ({
      real_images: acc.real_images + (curr.real_images || 0),
      positives: acc.positives + (curr.positives || 0),
      negatives: acc.negatives + (curr.negatives || 0),
      boxes: acc.boxes + (curr.boxes || 0),
      sequences: acc.sequences + (curr.sequences || 0),
    }),
    { real_images: 0, positives: 0, negatives: 0, boxes: 0, sequences: 0 }
  );

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <TableIcon className="w-5 h-5 mr-2 text-accent" />
          Source Level Accounting
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="overflow-x-auto rounded-lg border border-border-subtle">
        <table className="w-full text-sm text-left">
          <thead className="bg-bg-elevated text-text-secondary text-xs uppercase font-semibold">
            <tr>
              <th className="px-4 py-3">Source Name</th>
              <th className="px-4 py-3 text-right">Images</th>
              <th className="px-4 py-3 text-right">Positives</th>
              <th className="px-4 py-3 text-right">Negatives</th>
              <th className="px-4 py-3 text-right">Boxes</th>
              <th className="px-4 py-3 text-right">Sequences</th>
              <th className="px-4 py-3">Modality</th>
              <th className="px-4 py-3">Sensor</th>
              <th className="px-4 py-3">Peer Review</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle bg-bg-surface">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-bg-subtle transition-colors">
                <td className="px-4 py-3 font-medium text-text-primary">{row.source_name}</td>
                <td className="px-4 py-3 text-right font-mono">{row.real_images?.toLocaleString() ?? 0}</td>
                <td className="px-4 py-3 text-right font-mono">{row.positives?.toLocaleString() ?? 0}</td>
                <td className="px-4 py-3 text-right font-mono">{row.negatives?.toLocaleString() ?? 0}</td>
                <td className="px-4 py-3 text-right font-mono">{row.boxes?.toLocaleString() ?? 0}</td>
                <td className="px-4 py-3 text-right font-mono">{row.sequences?.toLocaleString() ?? 0}</td>
                <td className="px-4 py-3">{row.modality}</td>
                <td className="px-4 py-3">{row.sensor}</td>
                <td className="px-4 py-3">{row.peer_review_status}</td>
              </tr>
            ))}
            <tr className="bg-bg-elevated font-semibold border-t-2 border-border-default">
              <td className="px-4 py-3 text-text-primary">TOTALS</td>
              <td className="px-4 py-3 text-right font-mono">{totals.real_images.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono">{totals.positives.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono">{totals.negatives.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono">{totals.boxes.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono">{totals.sequences.toLocaleString()}</td>
              <td colSpan={3} className="px-4 py-3"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

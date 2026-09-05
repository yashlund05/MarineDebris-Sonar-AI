import React from "react";
import { Info, ThumbsUp, ThumbsDown, FileText, CheckCircle2 } from "lucide-react";
import { ModelExplanationResponse, ModelArtifactsResponse } from "../../types/modelEvaluation";

interface ExplainabilityAndArtifactsProps {
  explanation?: ModelExplanationResponse | null;
  artifactsResponse?: ModelArtifactsResponse | null;
}

export const ExplainabilityAndArtifacts: React.FC<ExplainabilityAndArtifactsProps> = ({
  explanation,
  artifactsResponse,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Acoustic Explanations */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center gap-2 border-b border-border-subtle pb-3">
          <Info className="w-4 h-4 text-accent" />
          <h3 className="text-sm font-bold text-text-primary">
            Acoustic Operating Characteristics & Evaluation Explanation
          </h3>
        </div>

        {explanation ? (
          <div className="space-y-4 text-xs">
            <div className="space-y-2">
              <span className="font-semibold text-emerald-800 flex items-center gap-1.5 font-mono">
                <ThumbsUp className="w-3.5 h-3.5 text-emerald-600" /> Operational Strengths
              </span>
              <ul className="space-y-1 pl-4 list-disc text-text-secondary">
                {explanation.strengths.map((s, idx) => (
                  <li key={idx} className="leading-relaxed">{s}</li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <span className="font-semibold text-rose-800 flex items-center gap-1.5 font-mono">
                <ThumbsDown className="w-3.5 h-3.5 text-rose-600" /> Operational Weaknesses & Constraints
              </span>
              <ul className="space-y-1 pl-4 list-disc text-text-secondary">
                {explanation.weaknesses.map((w, idx) => (
                  <li key={idx} className="leading-relaxed">{w}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-xs text-text-muted">No acoustic diagnostic notes recorded.</p>
        )}
      </div>

      {/* Verified Artifacts */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-text-primary">
              Physical Artifact Integrity & Provenance
            </h3>
          </div>
          <span className="text-xs font-mono text-text-muted">
            {artifactsResponse?.artifacts.filter((a) => a.exists).length || 0} /{" "}
            {artifactsResponse?.artifacts.length || 0} Verified
          </span>
        </div>

        <div className="space-y-2.5 overflow-y-auto max-h-60 pr-1">
          {artifactsResponse?.artifacts.map((art) => (
            <div
              key={art.path}
              className="p-3 bg-slate-50 border border-border-subtle rounded-xl flex items-center justify-between gap-3 text-xs"
            >
              <div className="space-y-0.5 overflow-hidden">
                <div className="flex items-center gap-2">
                  <span className="font-bold font-mono text-[11px] text-accent uppercase">
                    {art.type}
                  </span>
                  <span className="text-text-muted text-[11px]">•</span>
                  <span className="text-text-secondary text-[11px] truncate" title={art.path}>
                    {art.description || art.path}
                  </span>
                </div>
                {art.sha256 && (
                  <p className="font-mono text-[10px] text-text-muted truncate">
                    SHA256: {art.sha256}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0">
                {art.exists ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    FOUND
                  </span>
                ) : (
                  <span className="text-[11px] font-mono text-text-muted bg-slate-100 px-2 py-0.5 rounded">
                    MISSING
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

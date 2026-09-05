import React from "react";
import { ShieldAlert, ShieldCheck, CheckCircle2, XCircle } from "lucide-react";
import { PromotionDecisionResponse } from "../../types/modelEvaluation";

interface PromotionGateCardProps {
  promotion: PromotionDecisionResponse;
}

export const PromotionGateCard: React.FC<PromotionGateCardProps> = ({ promotion }) => {
  const gate = promotion.promotion_gate;
  const isRejected = gate?.status === "REJECTED" || !gate?.overall_pass;

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider font-mono">
            {isRejected ? (
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
            ) : (
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            )}
            Model Governance & Gate Intelligence
          </div>
          <h3 className="text-base font-bold text-text-primary mt-0.5">
            Automated Promotion Gate Audit Decision
          </h3>
        </div>

        <div>
          {promotion.is_production ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full text-xs font-semibold font-mono">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              CURRENT PRODUCTION BASELINE
            </span>
          ) : isRejected ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-50 border border-rose-200 text-rose-800 rounded-full text-xs font-semibold font-mono">
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              PROMOTION REJECTED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full text-xs font-semibold font-mono">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              PROMOTION ELIGIBLE
            </span>
          )}
        </div>
      </div>

      {gate ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {gate.checks.map((c) => (
              <div
                key={c.name}
                className={`p-4 rounded-xl border ${
                  c.passed
                    ? "bg-emerald-50/40 border-emerald-200/80 text-emerald-950"
                    : "bg-rose-50/50 border-rose-200/80 text-rose-950"
                } flex items-start justify-between gap-3`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {c.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                    )}
                    <span className="font-semibold text-xs font-mono">{c.name}</span>
                  </div>
                  <div className="text-[11px] font-mono space-y-0.5 pt-1 text-text-secondary">
                    <p>Required: <span className="font-semibold">{c.required}</span></p>
                    <p>Observed: <span className="font-bold text-text-primary">{c.observed}</span></p>
                  </div>
                </div>

                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    c.passed
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-rose-100 text-rose-800"
                  }`}
                >
                  {c.passed ? "PASS" : "FAIL"}
                </span>
              </div>
            ))}
          </div>

          <div className="p-4 bg-slate-50 border border-border-subtle rounded-xl space-y-1.5">
            <span className="text-xs font-bold font-mono text-text-primary block uppercase">
              Promotion Gate Rationale & Next Steps
            </span>
            <p className="text-xs text-text-secondary leading-relaxed">
              {promotion.rationale || gate.recommendation || "Evaluation gate criteria enforced per marine acoustic safety protocols."}
            </p>
          </div>
        </div>
      ) : (
        <p className="text-xs text-text-muted">No promotion gate audit evaluation available for this checkpoint.</p>
      )}
    </div>
  );
};

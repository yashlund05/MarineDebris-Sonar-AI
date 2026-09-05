import React from "react";
import { ConfidenceState } from "../../types/dataset";
import { ShieldCheck, BrainCircuit, MessageSquareWarning, XCircle, AlertTriangle } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface ConfidenceStateBadgeProps {
  state: ConfidenceState;
  className?: string;
}

export const ConfidenceStateBadge: React.FC<ConfidenceStateBadgeProps> = ({ state, className }) => {
  const config = {
    VERIFIED: {
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
      icon: ShieldCheck,
      label: "VERIFIED",
    },
    DERIVED: {
      color: "bg-sky-50 text-sky-700 border-sky-200",
      icon: BrainCircuit,
      label: "DERIVED",
    },
    DECLARED: {
      color: "bg-amber-50 text-amber-700 border-amber-200",
      icon: MessageSquareWarning,
      label: "DECLARED",
    },
    NOT_AVAILABLE: {
      color: "bg-slate-50 text-slate-600 border-slate-200",
      icon: XCircle,
      label: "NOT AVAILABLE",
    },
    CONFLICT: {
      color: "bg-rose-50 text-rose-700 border-rose-200",
      icon: AlertTriangle,
      label: "CONFLICT",
    },
  };

  const current = config[state] || config.NOT_AVAILABLE;
  const Icon = current.icon;

  return (
    <span
      className={twMerge(
        clsx(
          "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border uppercase tracking-wider",
          current.color,
          className
        )
      )}
    >
      <Icon className="w-3 h-3 mr-1" />
      {current.label}
    </span>
  );
};

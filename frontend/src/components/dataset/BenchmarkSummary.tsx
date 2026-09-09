import React from "react";
import { BenchmarkData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Target } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  benchmarks: Confident<BenchmarkData[]>;
}

export const BenchmarkSummary: React.FC<Props> = ({ benchmarks }) => {
  const { data, confidence } = benchmarks;

  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Target className="w-5 h-5 mr-2 text-accent" />
            Benchmark Performance
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const canonical = data.find(b => b.type === "CANONICAL");
  const operational = data.find(b => b.type === "OPERATIONAL");
  const canonicalEval = data.find(b => b.type === "CANONICAL_EVALUATION");

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Target className="w-5 h-5 mr-2 text-accent" />
            Benchmark Performance
          </h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Objective verification on frozen detector (conf=0.001 canonical vs conf=0.25 operational)
          </p>
        </div>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className={clsx("grid grid-cols-1 gap-6", canonicalEval ? "lg:grid-cols-3" : "lg:grid-cols-2")}>
        {canonical && (
          <BenchmarkCard 
            title="CANONICAL BENCHMARK"
            subtitle={`conf=${canonical.confidence_threshold}, IoU=${canonical.iou_threshold}`}
            data={canonical}
            colorTheme="sky"
          />
        )}
        {operational && (
          <BenchmarkCard 
            title="OPERATIONAL POINT"
            subtitle={`conf=${operational.confidence_threshold}, IoU=${operational.iou_threshold}`}
            data={operational}
            colorTheme="emerald"
          />
        )}
        {canonicalEval && (
          <BenchmarkCard 
            title="CANONICAL EVAL (BENCHMARK 5)"
            subtitle="External FLS/SSS Classes (0, 2, 3)"
            data={canonicalEval}
            colorTheme="purple"
          />
        )}
      </div>
    </div>
  );
};

const BenchmarkCard = ({ title, subtitle, data, colorTheme }: { title: string; subtitle: string; data: BenchmarkData; colorTheme: "sky" | "emerald" | "purple" }) => {
  const bgClass = colorTheme === "sky" 
    ? "bg-sky-50 border-sky-200" 
    : colorTheme === "emerald"
    ? "bg-emerald-50 border-emerald-200"
    : "bg-purple-50 border-purple-200";
  const textClass = colorTheme === "sky" ? "text-sky-900" : colorTheme === "emerald" ? "text-emerald-900" : "text-purple-900";
  const accentClass = colorTheme === "sky" ? "text-sky-600" : colorTheme === "emerald" ? "text-emerald-600" : "text-purple-600";
  const headerBgClass = colorTheme === "sky" ? "bg-sky-100/50" : colorTheme === "emerald" ? "bg-emerald-100/50" : "bg-purple-100/50";


  return (
    <div className={clsx("rounded-xl border overflow-hidden", bgClass)}>
      <div className={clsx("px-4 py-3 border-b flex justify-between items-center", headerBgClass, bgClass.split(" ")[1])}>
        <div>
          <h3 className={clsx("font-bold text-sm", textClass)}>{title}</h3>
          <p className={clsx("text-[11px] font-mono mt-0.5", accentClass)}>{subtitle}</p>
        </div>
        <div className={clsx("text-right text-[10px] font-mono uppercase", textClass)}>
          <div>{data.metrics.test_images.toLocaleString()} Test Imgs</div>
          <div>{data.metrics.test_objects.toLocaleString()} Test Objs</div>
        </div>
      </div>
      
      <div className="p-4 grid grid-cols-2 sm:grid-cols-5 gap-3">
        <MetricBox label="mAP50" value={data.metrics.mAP50} />
        <MetricBox label="Recall" value={data.metrics.recall} />
        <MetricBox label="Precision" value={data.metrics.precision} />
        <MetricBox label="F1 Score" value={data.metrics.f1} />
        <MetricBox label="mAP50-95" value={data.metrics.mAP50_95} />
      </div>
    </div>
  );
};

const MetricBox = ({ label, value }: { label: string; value: number }) => (
  <div className="flex flex-col items-center justify-center p-2 bg-white rounded-lg border border-slate-200 shadow-sm">
    <span className="text-[10px] font-bold text-slate-500 mb-1">{label}</span>
    <span className="text-lg font-mono font-semibold text-slate-900">
      {(value * 100).toFixed(1)}%
    </span>
  </div>
);

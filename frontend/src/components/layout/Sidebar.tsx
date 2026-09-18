import React from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, UploadCloud, Cpu, Layers, Activity, Waves, HardDrive, BarChart2, MapPinned, FlaskConical } from "lucide-react";
import { systemApi } from "../../api/client";

export const Sidebar: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 10000,
    retry: 1,
  });

  const isApiConnected = health?.status === "ok" || health?.status === "degraded";
  const isDbConnected = health?.database === "connected";

  const workspaceNav = [
    { to: "/", label: "Command center", icon: LayoutDashboard },
    { to: "/surveys", label: "Expeditions", icon: MapPinned },
    { to: "/upload", label: "Start an expedition", icon: UploadCloud },
  ];

  const intelligenceNav = [
    { to: "/enhancement", label: "Signal lab", icon: FlaskConical },
    { to: "/models", label: "Intelligence registry", icon: Cpu },
    { to: "/models/evaluation", label: "Model evidence", icon: BarChart2 },
    { to: "/dataset", label: "Dataset provenance", icon: Layers },
  ];

  return (
    <aside className="app-sidebar w-64 border-r border-border-subtle bg-bg-surface flex-col justify-between p-4 min-h-[calc(100vh-3.5rem)] select-none hidden lg:flex">
      <div className="space-y-6">
        {/* Workspace Section */}
        <div className="space-y-1">
          <div className="px-3 pb-1 text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            Fieldwork
          </div>
          {workspaceNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive ? "bg-[#19313A] text-[#FFF8EB] font-semibold shadow-sm" : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Intelligence Section */}
        <div className="space-y-1">
          <div className="px-3 pb-1 text-[11px] font-semibold text-text-muted uppercase tracking-wider font-mono">
            Intelligence
          </div>
          {intelligenceNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive ? "bg-[#19313A] text-[#FFF8EB] font-semibold shadow-sm" : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        <div className="sidebar-field-note p-3 bg-bg-elevated/60 rounded-xl border border-border-subtle text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 text-text-primary font-semibold text-[11px]">
            <Waves className="w-3.5 h-3.5 text-accent" />
            <span>Field notebook</span>
          </div>
          <p className="text-text-muted text-[11px] leading-relaxed">
            Your survey, its source frames, model version and report stay joined as one evidence record.
          </p>
        </div>
      </div>

      <div className="p-3 bg-bg-elevated/50 rounded-xl border border-border-subtle space-y-2 font-mono text-[11px]">
        <div className="flex items-center justify-between">
          <span className="text-text-muted flex items-center gap-1.5">
            <Activity className="w-3 h-3 text-text-muted" /> API Gateway
          </span>
          <span className="flex items-center gap-1 font-semibold">
            {isApiConnected ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-emerald-700">Online</span>
              </>
            ) : (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span className="text-rose-700">Offline</span>
              </>
            )}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-text-muted flex items-center gap-1.5">
            <HardDrive className="w-3 h-3 text-text-muted" /> Core Database
          </span>
          <span className="flex items-center gap-1 font-semibold">
            {isDbConnected ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-emerald-700">Connected</span>
              </>
            ) : (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span className="text-amber-800">Disconnected</span>
              </>
            )}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-text-muted flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-text-muted" /> ML Weights
          </span>
          <span className="flex items-center gap-1 font-semibold text-amber-800">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>{health?.active_detection_model ? "Registered" : "Awaiting"}</span>
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, UploadCloud, Database, Cpu, FileText } from "lucide-react";

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/upload", label: "Upload Survey", icon: UploadCloud },
    { to: "/surveys", label: "Survey Archive", icon: Database },
    { to: "/models", label: "Model Registry", icon: Cpu },
  ];

  return (
    <aside className="w-60 border-r border-border-subtle bg-bg-surface flex flex-col justify-between p-3 min-h-[calc(100vh-3.5rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold text-text-muted uppercase tracking-wider">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent text-white shadow-sm"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="p-3 bg-bg-elevated rounded-lg border border-border-subtle text-xs space-y-1.5">
        <div className="flex items-center space-x-1.5 text-text-primary font-semibold">
          <FileText className="w-3.5 h-3.5 text-accent" />
          <span>Engineering Phase</span>
        </div>
        <p className="text-text-secondary text-[11px] leading-relaxed">
          Phase 0: Engineering Foundation. Sonar ML pipeline is scheduled for Phase 1.
        </p>
      </div>
    </aside>
  );
};

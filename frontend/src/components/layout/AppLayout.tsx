import React from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";

export const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col font-sans antialiased app-shell">
      <Navbar />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="app-shell__main flex-1 min-w-0 p-4 md:p-6 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;

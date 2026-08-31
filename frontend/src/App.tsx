import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPlaceholderPage } from "./pages/DashboardPlaceholderPage";
import { UploadPlaceholderPage } from "./pages/UploadPlaceholderPage";
import { SurveysPlaceholderPage } from "./pages/SurveysPlaceholderPage";
import { ModelsPlaceholderPage } from "./pages/ModelsPlaceholderPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPlaceholderPage />} />
          <Route path="upload" element={<UploadPlaceholderPage />} />
          <Route path="surveys" element={<SurveysPlaceholderPage />} />
          <Route path="models" element={<ModelsPlaceholderPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

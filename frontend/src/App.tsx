import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { UploadPage } from "./pages/UploadPage";
import { SurveyListPage } from "./pages/SurveyListPage";
import { SurveyDetailPage } from "./pages/SurveyDetailPage";
import { ModelsPage } from "./pages/ModelsPage";
import { ModelEvaluationPage } from "./pages/ModelEvaluationPage";
import { DatasetPage } from "./pages/DatasetPage";
import { SonarEnhancementPage } from "./pages/SonarEnhancementPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="surveys" element={<SurveyListPage />} />
          <Route path="surveys/:id" element={<SurveyDetailPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="models/evaluation" element={<ModelEvaluationPage />} />
          <Route path="dataset" element={<DatasetPage />} />
          <Route path="enhancement" element={<SonarEnhancementPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

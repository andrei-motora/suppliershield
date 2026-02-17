import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import RiskRankings from "./pages/RiskRankings";
import WhatIfSimulator from "./pages/WhatIfSimulator";
import SensitivityAnalysis from "./pages/SensitivityAnalysis";
import Recommendations from "./pages/Recommendations";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <Routes>
      <Route path="upload" element={<Upload />} />
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="risk-rankings" element={<RiskRankings />} />
        <Route path="what-if" element={<WhatIfSimulator />} />
        <Route path="sensitivity" element={<SensitivityAnalysis />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

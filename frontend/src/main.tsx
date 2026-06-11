import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./ui/AppShell";
import { HomePage } from "./ui/HomePage";
import { EstimatePage } from "./ui/EstimatePage";
import { NewEstimatePage } from "./ui/NewEstimatePage";
import { RoomsPage } from "./ui/RoomsPage";
import { SharedEstimatePage } from "./ui/SharedEstimatePage";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/estimate/new" element={<NewEstimatePage />} />
          <Route path="/estimate/:estimateId/rooms" element={<RoomsPage />} />
          <Route path="/estimate/:estimateId" element={<EstimatePage />} />
          <Route path="/s/:shareToken" element={<SharedEstimatePage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  </React.StrictMode>
);

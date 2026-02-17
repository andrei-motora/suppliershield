import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Database, Upload as UploadIcon, Loader2, AlertCircle, Globe } from "lucide-react";
import FileDropZone from "../components/FileDropZone";
import { uploadFile, finalizeUpload, loadDemoData } from "../api/client";
import type { ValidationError } from "../types";

type FileStatus = "idle" | "uploading" | "success" | "error";

interface FileState {
  status: FileStatus;
  rowCount?: number;
  errorMessage?: string;
}

const REQUIRED_FILES = [
  {
    type: "suppliers",
    label: "Suppliers",
    columns: [
      "id", "name", "tier", "component", "country", "country_code",
      "region", "contract_value_eur_m", "lead_time_days",
      "financial_health", "past_disruptions", "has_backup",
    ],
  },
  {
    type: "dependencies",
    label: "Dependencies",
    columns: ["source_id", "target_id", "dependency_weight"],
  },
  {
    type: "product_bom",
    label: "Product BOM",
    columns: [
      "product_id", "product_name", "annual_revenue_eur_m",
      "component_supplier_ids",
    ],
  },
];

const OPTIONAL_FILES = [
  {
    type: "country_risk",
    label: "Country Risk (Optional)",
    columns: [
      "country", "country_code", "political_stability",
      "natural_disaster_freq", "trade_restriction_risk",
      "logistics_performance",
    ],
  },
];

type Step = "welcome" | "upload" | "processing";

export default function Upload() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("welcome");
  const [files, setFiles] = useState<Record<string, FileState>>({
    suppliers: { status: "idle" },
    dependencies: { status: "idle" },
    country_risk: { status: "idle" },
    product_bom: { status: "idle" },
  });
  const [processing, setProcessing] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [finalizeErrors, setFinalizeErrors] = useState<ValidationError[]>([]);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Only required files need to be uploaded to enable finalization
  const allUploaded = REQUIRED_FILES.every((f) => files[f.type].status === "success");

  const handleFileSelect = useCallback(async (fileType: string, file: File) => {
    setFiles((prev) => ({
      ...prev,
      [fileType]: { status: "uploading" },
    }));
    setFinalizeErrors([]);

    try {
      const result = await uploadFile(fileType, file);
      if (result.status === "success") {
        setFiles((prev) => ({
          ...prev,
          [fileType]: { status: "success", rowCount: result.row_count },
        }));
      } else {
        setFiles((prev) => ({
          ...prev,
          [fileType]: {
            status: "error",
            errorMessage: result.errors.join("; ") || "Validation failed",
          },
        }));
      }
    } catch (e) {
      setFiles((prev) => ({
        ...prev,
        [fileType]: {
          status: "error",
          errorMessage: e instanceof Error ? e.message : "Upload failed",
        },
      }));
    }
  }, []);

  const handleFinalize = useCallback(async () => {
    setProcessing(true);
    setFinalizeErrors([]);
    setGlobalError(null);

    try {
      const result = await finalizeUpload();
      if (result.status === "success") {
        navigate("/");
      } else {
        setFinalizeErrors(result.errors);
        setProcessing(false);
      }
    } catch (e) {
      setGlobalError(e instanceof Error ? e.message : "Processing failed");
      setProcessing(false);
    }
  }, [navigate]);

  const handleDemoLoad = useCallback(async () => {
    setDemoLoading(true);
    setGlobalError(null);

    try {
      const result = await loadDemoData();
      if (result.status === "success") {
        navigate("/");
      } else {
        setGlobalError("Failed to load demo data");
        setDemoLoading(false);
      }
    } catch (e) {
      setGlobalError(e instanceof Error ? e.message : "Failed to load demo data");
      setDemoLoading(false);
    }
  }, [navigate]);

  // ── Step 1: Welcome ──
  if (step === "welcome") {
    return (
      <div className="min-h-screen bg-shield-bg flex items-center justify-center p-6">
        <div className="max-w-lg w-full text-center space-y-8">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl bg-shield-accent/10 flex items-center justify-center">
              <Shield className="w-8 h-8 text-shield-accent" />
            </div>
          </div>

          <div>
            <h1 className="text-2xl font-bold text-shield-text">
              Welcome to SupplierShield
            </h1>
            <p className="text-shield-muted mt-2">
              Map your supply chain, score risk, and uncover hidden vulnerabilities.
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => setStep("upload")}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-shield-accent hover:bg-shield-accent/90 text-white rounded-lg font-medium transition-colors"
            >
              <UploadIcon className="w-5 h-5" />
              Upload Your Data
            </button>

            <button
              onClick={handleDemoLoad}
              disabled={demoLoading}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-shield-surface border border-shield-border hover:border-shield-accent/40 text-shield-text rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {demoLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Database className="w-5 h-5" />
              )}
              {demoLoading ? "Loading Sample Data..." : "Try with Sample Data"}
            </button>
          </div>

          {globalError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-400">
              {globalError}
            </div>
          )}

          <p className="text-xs text-shield-dim">
            Upload 3 CSV files (suppliers, dependencies, product BOM) to analyze your supply chain.
            Country risk data is built-in for 195 countries.
          </p>
        </div>
      </div>
    );
  }

  // ── Step 2: File Upload ──
  return (
    <div className="min-h-screen bg-shield-bg flex items-center justify-center p-6">
      <div className="max-w-2xl w-full space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-bold text-shield-text">Upload Your Data</h1>
          <p className="text-sm text-shield-muted mt-1">
            Upload 3 CSV files to build your supply chain model
          </p>
        </div>

        {/* Required files */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-shield-muted">
            <div className="h-px flex-1 bg-shield-border" />
            <span>Required</span>
            <div className="h-px flex-1 bg-shield-border" />
          </div>
          {REQUIRED_FILES.map((cfg) => (
            <FileDropZone
              key={cfg.type}
              fileType={cfg.type}
              label={cfg.label}
              expectedColumns={cfg.columns}
              status={files[cfg.type].status}
              rowCount={files[cfg.type].rowCount}
              errorMessage={files[cfg.type].errorMessage}
              onFileSelect={(file) => handleFileSelect(cfg.type, file)}
            />
          ))}
        </div>

        {/* Optional files */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-shield-dim">
            <div className="h-px flex-1 bg-shield-border/50" />
            <span>Optional</span>
            <div className="h-px flex-1 bg-shield-border/50" />
          </div>
          <div className="flex items-center gap-2 px-1 text-xs text-shield-dim">
            <Globe className="w-3.5 h-3.5 shrink-0" />
            <span>Built-in baseline covers 195 countries. Upload only to override specific values.</span>
          </div>
          {OPTIONAL_FILES.map((cfg) => (
            <FileDropZone
              key={cfg.type}
              fileType={cfg.type}
              label={cfg.label}
              expectedColumns={cfg.columns}
              status={files[cfg.type].status}
              rowCount={files[cfg.type].rowCount}
              errorMessage={files[cfg.type].errorMessage}
              onFileSelect={(file) => handleFileSelect(cfg.type, file)}
            />
          ))}
        </div>

        {finalizeErrors.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Validation Errors</span>
            </div>
            {finalizeErrors.map((err, i) => (
              <div key={i} className="text-xs text-red-300">
                <span className="font-mono text-red-400">{err.file}</span>
                {" — "}
                {err.message}
              </div>
            ))}
          </div>
        )}

        {globalError && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-400">
            {globalError}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => setStep("welcome")}
            className="px-4 py-2.5 bg-shield-surface border border-shield-border text-shield-muted rounded-lg text-sm hover:text-shield-text transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleFinalize}
            disabled={!allUploaded || processing}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 bg-shield-accent hover:bg-shield-accent/90 text-white rounded-lg font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {processing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Building Analytics...
              </>
            ) : (
              "Process Data"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

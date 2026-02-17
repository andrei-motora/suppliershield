import { useCallback, useRef, useState } from "react";
import { Upload, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

interface FileDropZoneProps {
  fileType: string;
  label: string;
  expectedColumns: string[];
  status: "idle" | "uploading" | "success" | "error";
  rowCount?: number;
  errorMessage?: string;
  onFileSelect: (file: File) => void;
}

export default function FileDropZone({
  fileType,
  label,
  expectedColumns,
  status,
  rowCount,
  errorMessage,
  onFileSelect,
}: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".csv")) {
        return;
      }
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const borderColor =
    status === "success"
      ? "border-green-500/40"
      : status === "error"
      ? "border-red-500/40"
      : isDragOver
      ? "border-shield-accent/60"
      : "border-shield-border";

  const bgColor =
    status === "success"
      ? "bg-green-500/5"
      : status === "error"
      ? "bg-red-500/5"
      : isDragOver
      ? "bg-shield-accent/5"
      : "bg-shield-surface";

  return (
    <div
      className={`${bgColor} border-2 border-dashed ${borderColor} rounded-lg p-5 transition-colors cursor-pointer`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => status !== "uploading" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />

      <div className="flex items-start gap-4">
        <div className="shrink-0 mt-0.5">
          {status === "uploading" && (
            <Loader2 className="w-6 h-6 text-shield-accent animate-spin" />
          )}
          {status === "success" && (
            <CheckCircle className="w-6 h-6 text-green-500" />
          )}
          {status === "error" && (
            <AlertCircle className="w-6 h-6 text-red-500" />
          )}
          {status === "idle" && (
            <Upload className="w-6 h-6 text-shield-muted" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-shield-text">{label}</p>
          <p className="text-xs text-shield-dim mt-0.5">
            {fileType}.csv
          </p>

          {status === "idle" && (
            <p className="text-xs text-shield-dim mt-2">
              Drop CSV here or click to browse
            </p>
          )}
          {status === "uploading" && (
            <p className="text-xs text-shield-accent mt-2">Uploading & validating...</p>
          )}
          {status === "success" && (
            <p className="text-xs text-green-400 mt-2">
              {rowCount} rows uploaded successfully
            </p>
          )}
          {status === "error" && (
            <p className="text-xs text-red-400 mt-2">{errorMessage}</p>
          )}

          <div className="mt-2">
            <p className="text-[10px] text-shield-dim">
              Expected columns: {expectedColumns.join(", ")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

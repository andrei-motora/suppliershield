import { Link } from "react-router-dom";
import { Upload } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  const isNoData = message?.includes("No data uploaded") || message?.includes("404");

  if (isNoData) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Upload className="w-10 h-10 text-shield-muted mb-4" />
        <p className="text-shield-text text-lg font-semibold mb-2">
          No Data Loaded
        </p>
        <p className="text-shield-muted text-sm mb-4">
          Upload your CSV files or load the sample dataset to get started.
        </p>
        <Link
          to="/upload"
          className="bg-shield-accent hover:bg-shield-accent/80 text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors"
        >
          Go to Upload
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-risk-critical text-lg font-semibold mb-2">
        Something went wrong
      </p>
      <p className="text-shield-muted text-sm mb-4">
        {message || "Failed to load data. Please try again."}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-shield-accent hover:bg-shield-accent/80 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

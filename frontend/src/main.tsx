import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

// Error boundary to catch render errors
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ color: "#ef4444", padding: 40, fontFamily: "monospace" }}>
          <h1>Application Error</h1>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {this.state.error.message}
            {"\n\n"}
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        // Don't retry auth or "no data" errors
        if (error && "status" in error) {
          const status = (error as { status: number }).status;
          if (status === 401 || status === 404) return false;
        }
        return failureCount < 1;
      },
    },
  },
});

try {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );
} catch (e) {
  document.getElementById("root")!.innerHTML =
    '<pre style="color:red;padding:40px;font-family:monospace">' +
    String(e) + "\n\n" + (e instanceof Error ? e.stack : "") +
    "</pre>";
}

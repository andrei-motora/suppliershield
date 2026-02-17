import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChatButton from "./ChatButton";
import ChatPanel from "./ChatPanel";

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-shield-bg">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-shield-border bg-shield-surface">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-shield-muted hover:text-shield-text p-1"
            aria-label="Open menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="font-bold text-shield-text">SupplierShield</span>
        </header>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>

      <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
      <ChatButton isOpen={chatOpen} onClick={() => setChatOpen((o) => !o)} />
    </div>
  );
}

import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  BarChart3,
  FlaskConical,
  Crosshair,
  ClipboardCheck,
  Shield,
  X,
  Upload,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV_SECTIONS: { heading?: string; items: NavItem[] }[] = [
  {
    heading: "Overview",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard },
    ],
  },
  {
    heading: "Analysis",
    items: [
      { to: "/risk-rankings", label: "Risk Rankings", icon: BarChart3 },
      { to: "/sensitivity", label: "Sensitivity", icon: Crosshair },
    ],
  },
  {
    heading: "Actions",
    items: [
      { to: "/what-if", label: "What-If Simulator", icon: FlaskConical },
      { to: "/recommendations", label: "Recommendations", icon: ClipboardCheck },
    ],
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed md:sticky top-0 left-0 z-50
          w-60 shrink-0 bg-shield-surface border-r border-shield-border
          flex flex-col h-screen
          transition-transform duration-200 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-shield-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Shield className="w-6 h-6 text-shield-accent" />
            <div>
              <h1 className="text-lg font-bold text-shield-text leading-tight">
                SupplierShield
              </h1>
              <p className="text-[10px] text-shield-muted leading-tight">
                Supply Chain Risk Analyzer
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="md:hidden text-shield-muted hover:text-shield-text p-1"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload / New Dataset link */}
        <div className="px-3 pt-3">
          <NavLink
            to="/upload"
            onClick={onClose}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-shield-accent hover:bg-shield-accent/10 border border-shield-accent/20 transition-colors"
          >
            <Upload className="w-4 h-4 shrink-0" />
            <span>New Dataset</span>
          </NavLink>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-3 overflow-y-auto">
          {NAV_SECTIONS.map((section, si) => (
            <div key={si} className={si > 0 ? "mt-5" : ""}>
              {section.heading && (
                <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-shield-dim">
                  {section.heading}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                        isActive
                          ? "bg-shield-accent/10 text-shield-accent font-medium border border-shield-accent/20"
                          : "text-shield-muted hover:text-shield-text hover:bg-white/[0.03]"
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-shield-border text-[10px] text-shield-dim flex items-center justify-between">
          <span>SupplierShield v2.0</span>
          <span>&copy; {new Date().getFullYear()}</span>
        </div>
      </aside>
    </>
  );
}

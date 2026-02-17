import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-shield-accent hover:bg-shield-accent/80 text-white font-semibold",
  secondary:
    "bg-shield-surface border border-shield-border hover:border-shield-accent/40 text-shield-muted hover:text-shield-text",
  ghost:
    "text-shield-muted hover:text-shield-text hover:bg-white/[0.04]",
  danger:
    "bg-risk-critical/10 border border-risk-critical/20 text-risk-critical hover:bg-risk-critical/20 font-medium",
};

export default function Button({
  variant = "secondary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`px-4 py-2 rounded-md text-sm transition-colors disabled:opacity-40 disabled:pointer-events-none ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

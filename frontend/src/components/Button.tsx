import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  icon?: ReactNode;
  loading?: boolean;
}

export function Button({
  children,
  className = "",
  icon,
  loading = false,
  type = "button",
  variant = "secondary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button-${variant} ${className}`.trim()}
      disabled={loading || props.disabled}
      type={type}
      {...props}
    >
      {icon}
      <span>{loading ? "Загрузка..." : children}</span>
    </button>
  );
}

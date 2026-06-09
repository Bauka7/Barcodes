import type { ReactNode } from "react";

interface TableProps {
  children: ReactNode;
  className?: string;
}

export function Table({ children, className = "" }: TableProps) {
  return (
    <div className={`table-wrap ${className}`.trim()}>
      <table>{children}</table>
    </div>
  );
}
